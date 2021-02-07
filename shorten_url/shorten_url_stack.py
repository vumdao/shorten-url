from aws_cdk import (
    core,
    aws_lambda as lambda_,
    aws_apigateway as api_gw,
    aws_dynamodb as ddb,
    aws_route53 as _route53,
    aws_route53_targets as _route53_target,
    aws_iam as iam,
)
import aws_cdk.aws_certificatemanager as _acm
import json


class ShortenUrlStack:
    def __init__(self):
        app = core.App()
        _env = core.Environment(region="ap-northeast-2")

        ddb_stack = ShortURLDDB(app, id=f"ShortenUrlDDB", env=_env)

        iam_stack = UrlShortenIAMRole(app, id='ShortenUrlIAMRole', ddb_table=ddb_stack.ddb_table_arn)

        redirect_lambda_stack = ShortenUrlRedirectLambda(app, id=f"ShortenURLRedirectLambda", env=_env,
                                                         ddb_table=ddb_stack.ddb_table_name, role=iam_stack.iam_role)

        create_lambda_stack = ShortenUrlCreateUrlLambda(app, id=f"ShortenURLCreateLambda", env=_env,
                                                        ddb_table=ddb_stack.ddb_table_name, role=iam_stack.iam_role)

        ShortenUrlApiGWStack(app, id=f"ShortenURLApiGW", env=_env,
                             redirect_handler=redirect_lambda_stack.handler,
                             create_handler=create_lambda_stack.handler)


class ShortURLDDB(core.Stack):
    """
    Dynamodb to store the long url and short url
    - Primary partition key: id (String)
    - Indexes: long-url-index
    """

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.ddb_table_name = None
        self.ddb_table_arn = None

        url_shortener_ddb = ddb.Table(
            self,
            id='ShortenURLDDB',
            table_name='dev-url-shortener',
            partition_key=ddb.Attribute(name='id', type=ddb.AttributeType.STRING),
            time_to_live_attribute='expiry_date'
        )
        self.ddb_table_name = url_shortener_ddb.table_name
        self.ddb_table_arn = url_shortener_ddb.table_arn

        write_capacity_scaling = url_shortener_ddb.auto_scale_write_capacity(
            max_capacity=40000,
            min_capacity=5
        )

        write_capacity_scaling.scale_on_utilization(
            target_utilization_percent=70
        )

        read_capapcity_scaling = url_shortener_ddb.auto_scale_read_capacity(
            max_capacity=40000,
            min_capacity=5
        )

        read_capapcity_scaling.scale_on_utilization(
            target_utilization_percent=70
        )

        """ Create index long-url-index """
        url_shortener_ddb.add_global_secondary_index(
            index_name='long-url-index',
            partition_key=ddb.Attribute(name='long_url', type=ddb.AttributeType.STRING)
        )

        global_index_write_capapcity_scaling = url_shortener_ddb.auto_scale_global_secondary_index_write_capacity(
            index_name='long-url-index',
            max_capacity=40000,
            min_capacity=5
        )

        global_index_write_capapcity_scaling.scale_on_utilization(
            target_utilization_percent=70
        )

        global_index_read_capapcity_scaling = url_shortener_ddb.auto_scale_global_secondary_index_read_capacity(
            index_name='long-url-index',
            max_capacity=40000,
            min_capacity=5
        )

        global_index_read_capapcity_scaling.scale_on_utilization(
            target_utilization_percent=70
        )


class UrlShortenIAMRole(core.Stack):
    """ Create IAM role for lambda to read/write Dynamodb """
    def __init__(self, scope: core.Construct, id: str, ddb_table, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        lambda_inline_policy = iam.PolicyDocument.from_json(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Resource": "*"
                    },
                    {
                        "Sid": "DDB",
                        "Effect": "Allow",
                        "Action": [
                            "dynamodb:PutItem",
                            "dynamodb:ListTables",
                            "dynamodb:GetItem",
                            "dynamodb:Scan",
                            "dynamodb:Query",
                            "dynamodb:UpdateItem",
                            "dynamodb:UpdateGlobalTable",
                            "dynamodb:UpdateTable",
                            "dynamodb:GetRecords",
                            "dynamodb:BatchGetItem",
                            "dynamodb:BatchWriteItem"
                        ],
                        "Resource": [
                            f"{ddb_table}",
                            f"{ddb_table}/index/*"
                        ]
                    }
                ]
            }
        )

        self.iam_role = iam.Role(
            scope=self, id='ShortenUrlIAMRole',
            role_name='shortenURLLambda',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            inline_policies={'ShortenURLLambdaDDB': lambda_inline_policy}
        )


class ShortenUrlRedirectLambda(core.Stack):
    """ Redirect lambda function: Return the original URL mapping to the shorten one """
    def __init__(self, scope: core.Construct, id: str, ddb_table, role, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.handler = lambda_.Function(
            scope=self,
            id=f'ShortenURLRedirectHandler',
            function_name='dev-url-shortener-redirect',
            runtime=lambda_.Runtime.PYTHON_3_8,
            code=lambda_.Code.from_asset("redirect_src"),
            handler="redirectUrl.handler",
            environment=dict(DYNAMODB_TABLE_NAME=ddb_table),
            role=role
        )


class ShortenUrlCreateUrlLambda(core.Stack):
    """ Lambda function to create short URL from long url """
    def __init__(self, scope: core.Construct, id: str, ddb_table, role, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.handler = lambda_.Function(
            scope=self,
            id=f'ShortenURLCreateHandler',
            function_name='dev-url-shortener-create',
            runtime=lambda_.Runtime.PYTHON_3_8,
            code=lambda_.Code.from_asset("create_src"),
            handler="createShortUrl.handler",
            environment=dict(DYNAMODB_TABLE_NAME=ddb_table,
                             APP_URL='https://s.cloudopz.co',
                             DYNAMODB_TABLE_LONG_URL_INDEX_NAME='long-url-index'),
            role=role
        )


class ShortenUrlApiGWStack(core.Stack):
    """ Create API GW """
    def __init__(self, scope: core.Construct, id: str, redirect_handler, create_handler, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        base_api = api_gw.RestApi(
            scope=self,
            id='ShortenURLAPI',
            rest_api_name='dev-url-shortener-api',
            deploy=True,
            deploy_options=api_gw.StageOptions(stage_name='devShortenURL')
        )

        # shortenUrl
        shorten_url = base_api.root.add_resource('shortenUrl')

        shorten_url_responses = [
            api_gw.MethodResponse(
                status_code='200',
                response_models={"application/json": api_gw.Model.EMPTY_MODEL},
                response_parameters={'method.response.header.Access-Control-Allow-Origin': True}
            ),
            api_gw.MethodResponse(
                status_code='500',
                response_models={"application/json": api_gw.Model.ERROR_MODEL},
            )
        ]
        shorten_url_lambda_integration = api_gw.LambdaIntegration(
            handler=create_handler,
            request_templates={"application/json": '{ "statusCode": "200" }'},
            integration_responses=[
                api_gw.IntegrationResponse(
                    status_code='200',
                    response_templates={'application/json': ''}
                )
            ]
        )
        shorten_url.add_method(
            http_method='POST',
            api_key_required=False,
            integration=shorten_url_lambda_integration,
            method_responses=shorten_url_responses
        )

        shorten_url_integration_mock = api_gw.MockIntegration(
            request_templates={"application/json": json.dumps({"statusCode": 200})},
            integration_responses=[
                api_gw.IntegrationResponse(
                    status_code='200',
                    response_templates={'application/json': ''},
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Methods": "'OPTIONS,POST'",
                        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                    },
                )
            ],
            passthrough_behavior=api_gw.PassthroughBehavior.WHEN_NO_MATCH
        )
        shorten_url_mock_reponses = api_gw.MethodResponse(
            status_code='200',
            response_models={
                "application/json": api_gw.Model.EMPTY_MODEL
            },
            response_parameters={
                "method.response.header.Access-Control-Allow-Methods": True,
                "method.response.header.Access-Control-Allow-Headers": True,
                "method.response.header.Access-Control-Allow-Origin": True
            }
        )
        shorten_url.add_method(
            http_method='OPTIONS',
            integration=shorten_url_integration_mock,
            method_responses=[shorten_url_mock_reponses]
        )

        # {id}
        id_url = base_api.root.add_resource("{id}")

        id_url_responses = [
            api_gw.MethodResponse(
                status_code='200',
                response_models={"application/json": api_gw.Model.EMPTY_MODEL},
                response_parameters={'method.response.header.Access-Control-Allow-Origin': True}
            )
        ]
        id_url_lambda_integration = api_gw.LambdaIntegration(
            handler=redirect_handler,
            request_templates={"application/json": '{ "statusCode": "200" }'},
            integration_responses=[
                api_gw.IntegrationResponse(
                    status_code='200',
                    response_templates={'application/json': ''}
                )
            ]
        )
        id_url.add_method(
            http_method='GET',
            integration=id_url_lambda_integration,
            method_responses=id_url_responses,
            request_parameters={'method.request.path.proxy': True}
        )

        id_url_integration_mock = api_gw.MockIntegration(
            request_templates={"application/json": json.dumps({"statusCode": 200})},
            integration_responses=[
                api_gw.IntegrationResponse(
                    status_code='200',
                    response_templates={'application/json': ''},
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Methods": "'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'",
                        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                    },
                )
            ],
            passthrough_behavior=api_gw.PassthroughBehavior.WHEN_NO_MATCH
        )
        id_url_mock_responses = api_gw.MethodResponse(
            status_code='200',
            response_models={
                "application/json": api_gw.Model.EMPTY_MODEL
            },
            response_parameters={
                "method.response.header.Access-Control-Allow-Methods": True,
                "method.response.header.Access-Control-Allow-Headers": True,
                "method.response.header.Access-Control-Allow-Origin": True
            }
        )
        id_url.add_method(
            http_method='OPTIONS',
            integration=id_url_integration_mock,
            method_responses=[id_url_mock_responses]
        )

        # Create custom domain mapping API
        sel_cert_arn = "arn:aws:acm:ap-northeast-2:111111111111:certificate/b1111bf5-ae1b-1f61-a111-f1d839428f5f"
        apigw_domain = base_api.add_domain_name(
            id='ShortenURLIDCustomDomain',
            certificate=_acm.Certificate.from_certificate_arn(
                scope=self,
                id="ShortenURLIDCert",
                certificate_arn=sel_cert_arn
            ),
            security_policy=api_gw.SecurityPolicy.TLS_1_2,
            domain_name='s.cloudopz.co'
        )

        dev_hosted_zone = 'A11AA1A1A1AAAA'
        hz_dev = _route53.HostedZone.from_hosted_zone_attributes(
            self, id="ShortenURLHostedZoneDev", hosted_zone_id=dev_hosted_zone, zone_name='cloudopz.co')

        _route53.ARecord(
            self, 'ShortenURLRoute53',
            record_name='s',
            zone=hz_dev,
            target=_route53.RecordTarget.from_alias(_route53_target.ApiGatewayDomain(apigw_domain))
        )
