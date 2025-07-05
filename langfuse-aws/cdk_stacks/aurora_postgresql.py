#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_logs,
  aws_rds,
  aws_secretsmanager
)

from constructs import Construct


class AuroraPostgresqlStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    db_cluster_name = self.node.try_get_context('db_cluster_name') or 'langfuse-db'
    database_config = self.node.try_get_context('database_config') or {}
    use_rds = database_config.get('use_rds_instead_of_aurora', False)

    sg_postgresql_client = aws_ec2.SecurityGroup(self, 'PostgreSQLClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for postgresql client',
      security_group_name=f'{db_cluster_name}-postgresql-client-sg'
    )
    cdk.Tags.of(sg_postgresql_client).add('Name', 'postgresql-client-sg')

    sg_postgresql_server = aws_ec2.SecurityGroup(self, 'PostgreSQLServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for postgresql',
      security_group_name=f'{db_cluster_name}-postgresql-server-sg'
    )
    sg_postgresql_server.add_ingress_rule(peer=sg_postgresql_client, connection=aws_ec2.Port.tcp(5432),
      description='postgresql-client-sg')
    sg_postgresql_server.add_ingress_rule(peer=sg_postgresql_server, connection=aws_ec2.Port.all_tcp(),
      description='postgresql-server-sg')
    cdk.Tags.of(sg_postgresql_server).add('Name', 'postgresql-server-sg')

    rds_subnet_group = aws_rds.SubnetGroup(self, 'PostgreSQLSubnetGroup',
      description='subnet group for postgresql',
      subnet_group_name=f'postgresql-{self.stack_name}',
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      vpc=vpc
    )

    #XXX: In order to exclude punctuations when generating a password
    # use aws_secretsmanager.Secret instead of aws_rds.DatabaseSecret.
    # Othwerise, an error occurred such as:
    # "All characters of the desired type have been excluded"
    db_secret = aws_secretsmanager.Secret(self, 'DatabaseSecret',
      generate_secret_string=aws_secretsmanager.SecretStringGenerator(
        secret_string_template=json.dumps({"username": "postgres"}),
        generate_string_key="password",
        exclude_punctuation=True,
        password_length=8
      )
    )
    rds_credentials = aws_rds.Credentials.from_secret(db_secret)

    if use_rds:
      # Use RDS PostgreSQL for cost optimization
      instance_type = database_config.get('instance_type', 'db.t4g.micro')
      allocated_storage = database_config.get('allocated_storage', 10)
      storage_type = database_config.get('storage_type', 'gp3')
      multi_az = database_config.get('multi_az', False)
      backup_retention_days = database_config.get('backup_retention_days', 1)
      engine_version = database_config.get('engine_version', '15.4')

      rds_engine = aws_rds.DatabaseInstanceEngine.postgres(
        version=aws_rds.PostgresEngineVersion.VER_15_8
      )

      # Create parameter group for RDS instance
      rds_param_group = aws_rds.ParameterGroup(self, 'RDSPostgreSQLParamGroup',
        engine=rds_engine,
        description='Custom parameter group for postgresql15',
        parameters={
          'log_min_duration_statement': '15000', # 15 sec
          'default_transaction_isolation': 'read committed',
          'client_encoding': 'UTF8'
        }
      )

      # Create RDS instance instead of Aurora cluster
      database_instance = aws_rds.DatabaseInstance(self, 'Database',
        engine=rds_engine,
        credentials=rds_credentials,
        instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.T4G, aws_ec2.InstanceSize.MICRO),
        allocated_storage=allocated_storage,
        storage_type=aws_rds.StorageType[storage_type.upper()],
        multi_az=multi_az,
        instance_identifier=db_cluster_name,
        database_name='langfuse',
        subnet_group=rds_subnet_group,
        parameter_group=rds_param_group,
        backup_retention=cdk.Duration.days(backup_retention_days),
        preferred_backup_window="03:00-04:00",
        preferred_maintenance_window="mon:04:00-mon:05:00",
        cloudwatch_logs_retention=aws_logs.RetentionDays.ONE_DAY,  # Minimal for dev
        security_groups=[sg_postgresql_server],
        vpc=vpc,
        vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
        deletion_protection=False,  # For dev environment
        removal_policy=cdk.RemovalPolicy.DESTROY,  # For dev environment
        auto_minor_version_upgrade=False
      )

      self.sg_rds_client = sg_postgresql_client
      self.database_secret = database_instance.secret
      self.database = database_instance

      # Output compatible with Aurora cluster endpoints
      cdk.CfnOutput(self, 'DBClusterEndpoint',
        value=database_instance.instance_endpoint.socket_address,
        export_name=f'{self.stack_name}-DBClusterEndpoint')
      cdk.CfnOutput(self, 'DBClusterReadEndpoint',
        value=database_instance.instance_endpoint.socket_address,  # Same for single instance
        export_name=f'{self.stack_name}-DBClusterReadEndpoint')

    else:
      # Original Aurora implementation
      rds_engine = aws_rds.DatabaseClusterEngine.aurora_postgres(version=aws_rds.AuroraPostgresEngineVersion.VER_15_4)

      #XXX: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Reference.ParameterGroups.html#AuroraPostgreSQL.Reference.Parameters.Cluster
      rds_cluster_param_group = aws_rds.ParameterGroup(self, 'AuroraPostgreSQLClusterParamGroup',
        engine=rds_engine,
        description='Custom cluster parameter group for aurora-postgresql15',
        parameters={
          'log_min_duration_statement': '15000', # 15 sec
          'default_transaction_isolation': 'read committed',
          'client_encoding': 'UTF8'
        }
      )

      #XXX: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Reference.ParameterGroups.html#AuroraPostgreSQL.Reference.Parameters.Instance
      rds_db_param_group = aws_rds.ParameterGroup(self, 'AuroraPostgreSQLDBParamGroup',
        engine=rds_engine,
        description='Custom parameter group for aurora-postgresql15',
        parameters={
          'log_min_duration_statement': '15000', # 15 sec
          'default_transaction_isolation': 'read committed'
        }
      )

      db_cluster = aws_rds.DatabaseCluster(self, 'Database',
        engine=rds_engine,
        credentials=rds_credentials, # A username of 'admin' (or 'postgres' for PostgreSQL) and SecretsManager-generated password
        writer=aws_rds.ClusterInstance.provisioned("writer",
          instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.R6G, aws_ec2.InstanceSize.LARGE),
          parameter_group=rds_db_param_group,
          auto_minor_version_upgrade=False,
        ),
        readers=[
          aws_rds.ClusterInstance.provisioned("reader",
            instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.R6G, aws_ec2.InstanceSize.LARGE),
            parameter_group=rds_db_param_group,
            auto_minor_version_upgrade=False
          )
        ],
        parameter_group=rds_cluster_param_group,
        cloudwatch_logs_retention=aws_logs.RetentionDays.THREE_DAYS,
        cluster_identifier=db_cluster_name,
        subnet_group=rds_subnet_group,
        backup=aws_rds.BackupProps(
          retention=cdk.Duration.days(3),
          preferred_window="03:00-04:00"
        ),
        security_groups=[sg_postgresql_server],
        vpc=vpc,
        vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)
      )

      self.sg_rds_client = sg_postgresql_client
      self.database_secret = db_cluster.secret
      self.database = db_cluster

      cdk.CfnOutput(self, 'DBClusterEndpoint',
        value=db_cluster.cluster_endpoint.socket_address,
        export_name=f'{self.stack_name}-DBClusterEndpoint')
      cdk.CfnOutput(self, 'DBClusterReadEndpoint',
        value=db_cluster.cluster_read_endpoint.socket_address,
        export_name=f'{self.stack_name}-DBClusterReadEndpoint')

    cdk.CfnOutput(self, 'RDSClientSecurityGroupId',
      value=sg_postgresql_client.security_group_id,
      export_name=f'{self.stack_name}-RDSClientSecurityGroupId')
    cdk.CfnOutput(self, 'DBSecretName',
      value=self.database_secret.secret_name,
      export_name=f'{self.stack_name}-DBSecretName')