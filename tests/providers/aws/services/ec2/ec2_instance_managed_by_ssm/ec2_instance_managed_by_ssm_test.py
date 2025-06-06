from unittest import mock

from boto3 import resource
from moto import mock_aws

from prowler.providers.aws.services.ssm.ssm_service import ManagedInstance
from tests.providers.aws.utils import (
    AWS_ACCOUNT_NUMBER,
    AWS_REGION_EU_WEST_1,
    AWS_REGION_US_EAST_1,
    set_mocked_aws_provider,
)

EXAMPLE_AMI_ID = "ami-12c6146b"


class Test_ec2_instance_managed_by_ssm_test:
    @mock_aws
    def test_ec2_no_instances(self):
        from prowler.providers.aws.services.ec2.ec2_service import EC2

        aws_provider = set_mocked_aws_provider(
            [AWS_REGION_EU_WEST_1, AWS_REGION_US_EAST_1]
        )

        ssm_client = mock.MagicMock
        ssm_client.managed_instances = {}

        with (
            mock.patch(
                "prowler.providers.common.provider.Provider.get_global_provider",
                return_value=aws_provider,
            ),
            mock.patch(
                "prowler.providers.aws.services.ssm.ssm_service.SSM",
                new=ssm_client,
            ),
            mock.patch(
                "prowler.providers.aws.services.ssm.ssm_client.ssm_client",
                new=ssm_client,
            ),
            mock.patch(
                "prowler.providers.aws.services.ec2.ec2_instance_managed_by_ssm.ec2_instance_managed_by_ssm.ec2_client",
                new=EC2(aws_provider),
            ),
        ):
            # Test Check
            from prowler.providers.aws.services.ec2.ec2_instance_managed_by_ssm.ec2_instance_managed_by_ssm import (
                ec2_instance_managed_by_ssm,
            )

            check = ec2_instance_managed_by_ssm()
            result = check.execute()

            assert len(result) == 0

    @mock_aws
    def test_ec2_instance_managed_by_ssm_non_compliance_instance(self):
        ssm_client = mock.MagicMock
        ssm_client.managed_instances = {}

        ec2 = resource("ec2", region_name=AWS_REGION_US_EAST_1)
        instance = ec2.create_instances(
            ImageId=EXAMPLE_AMI_ID,
            MinCount=1,
            MaxCount=1,
            UserData="This is some user_data",
        )[0]

        ssm_client = mock.MagicMock
        ssm_client.managed_instances = {}

        from prowler.providers.aws.services.ec2.ec2_service import EC2

        aws_provider = set_mocked_aws_provider(
            [AWS_REGION_EU_WEST_1, AWS_REGION_US_EAST_1]
        )

        with (
            mock.patch(
                "prowler.providers.common.provider.Provider.get_global_provider",
                return_value=aws_provider,
            ),
            mock.patch(
                "prowler.providers.aws.services.ssm.ssm_service.SSM",
                new=ssm_client,
            ),
            mock.patch(
                "prowler.providers.aws.services.ssm.ssm_client.ssm_client",
                new=ssm_client,
            ),
            mock.patch(
                "prowler.providers.aws.services.ec2.ec2_instance_managed_by_ssm.ec2_instance_managed_by_ssm.ec2_client",
                new=EC2(aws_provider),
            ),
        ):
            # Test Check
            from prowler.providers.aws.services.ec2.ec2_instance_managed_by_ssm.ec2_instance_managed_by_ssm import (
                ec2_instance_managed_by_ssm,
            )

            check = ec2_instance_managed_by_ssm()
            result = check.execute()

            assert len(result) == 1
            assert result[0].status == "FAIL"
            assert result[0].region == AWS_REGION_US_EAST_1
            assert result[0].resource_tags is None
            assert (
                result[0].status_extended
                == f"EC2 Instance {instance.id} is not managed by Systems Manager."
            )
            assert result[0].resource_id == instance.id

    @mock_aws
    def test_ec2_instance_managed_by_ssm_compliance_instance(self):
        ec2 = resource("ec2", region_name=AWS_REGION_US_EAST_1)
        instance = ec2.create_instances(
            ImageId=EXAMPLE_AMI_ID,
            MinCount=1,
            MaxCount=1,
            UserData="This is some user_data",
        )[0]

        ssm_client = mock.MagicMock
        ssm_client.managed_instances = {
            instance.id: ManagedInstance(
                arn=f"arn:aws:ec2:{AWS_REGION_US_EAST_1}:{AWS_ACCOUNT_NUMBER}:instance/{instance.id}",
                id=instance.id,
                region=AWS_REGION_US_EAST_1,
            )
        }

        from prowler.providers.aws.services.ec2.ec2_service import EC2

        aws_provider = set_mocked_aws_provider(
            [AWS_REGION_EU_WEST_1, AWS_REGION_US_EAST_1]
        )

        with (
            mock.patch(
                "prowler.providers.common.provider.Provider.get_global_provider",
                return_value=aws_provider,
            ),
            mock.patch(
                "prowler.providers.aws.services.ssm.ssm_service.SSM",
                new=ssm_client,
            ),
            mock.patch(
                "prowler.providers.aws.services.ssm.ssm_client.ssm_client",
                new=ssm_client,
            ),
            mock.patch(
                "prowler.providers.aws.services.ec2.ec2_instance_managed_by_ssm.ec2_instance_managed_by_ssm.ec2_client",
                new=EC2(aws_provider),
            ),
        ):
            # Test Check
            from prowler.providers.aws.services.ec2.ec2_instance_managed_by_ssm.ec2_instance_managed_by_ssm import (
                ec2_instance_managed_by_ssm,
            )

            check = ec2_instance_managed_by_ssm()
            result = check.execute()

            assert len(result) == 1
            assert result[0].status == "PASS"
            assert result[0].region == AWS_REGION_US_EAST_1
            assert result[0].resource_tags is None
            assert (
                result[0].status_extended
                == f"EC2 Instance {instance.id} is managed by Systems Manager."
            )
            assert result[0].resource_id == instance.id

    @mock_aws
    def test_ec2_instance_managed_by_ssm_running(self):
        ec2 = resource("ec2", region_name=AWS_REGION_US_EAST_1)
        instances_pending = ec2.create_instances(
            ImageId=EXAMPLE_AMI_ID,
            MinCount=2,
            MaxCount=2,
            UserData="This is some user_data",
        )
        instance_managed = ec2.Instance(instances_pending[0].id)
        instance_unmanaged = ec2.Instance(instances_pending[1].id)
        assert instance_managed.state["Name"] == "running"
        assert instance_unmanaged.state["Name"] == "running"

        ssm_client = mock.MagicMock
        ssm_client.managed_instances = {
            instance_managed.id: ManagedInstance(
                arn=f"arn:aws:ec2:{AWS_REGION_US_EAST_1}:{AWS_ACCOUNT_NUMBER}:instance/{instance_managed.id}",
                id=instance_managed.id,
                region=AWS_REGION_US_EAST_1,
            )
        }

        from prowler.providers.aws.services.ec2.ec2_service import EC2

        aws_provider = set_mocked_aws_provider(
            [AWS_REGION_EU_WEST_1, AWS_REGION_US_EAST_1]
        )

        with (
            mock.patch(
                "prowler.providers.common.provider.Provider.get_global_provider",
                return_value=aws_provider,
            ),
            mock.patch(
                "prowler.providers.aws.services.ssm.ssm_service.SSM",
                new=ssm_client,
            ),
            mock.patch(
                "prowler.providers.aws.services.ssm.ssm_client.ssm_client",
                new=ssm_client,
            ),
            mock.patch(
                "prowler.providers.aws.services.ec2.ec2_instance_managed_by_ssm.ec2_instance_managed_by_ssm.ec2_client",
                new=EC2(aws_provider),
            ),
        ):
            # Test Check
            from prowler.providers.aws.services.ec2.ec2_instance_managed_by_ssm.ec2_instance_managed_by_ssm import (
                ec2_instance_managed_by_ssm,
            )

            check = ec2_instance_managed_by_ssm()
            results = check.execute()

            assert len(results) == 2
            for result in results:
                if result.resource_id == instance_managed.id:
                    assert result.status == "PASS"
                    assert result.region == AWS_REGION_US_EAST_1
                    assert result.resource_tags is None
                    assert (
                        result.status_extended
                        == f"EC2 Instance {instance_managed.id} is managed by Systems Manager."
                    )

                if result.resource_id == instance_unmanaged.id:
                    assert result.status == "FAIL"
                    assert result.region == AWS_REGION_US_EAST_1
                    assert result.resource_tags is None
                    assert (
                        result.status_extended
                        == f"EC2 Instance {instance_unmanaged.id} is not managed by Systems Manager."
                    )

    @mock_aws
    def test_ec2_instance_managed_by_ssm_stopped(self):
        ec2 = resource("ec2", region_name=AWS_REGION_US_EAST_1)
        instances_pending = ec2.create_instances(
            ImageId=EXAMPLE_AMI_ID,
            MinCount=1,
            MaxCount=1,
            UserData="This is some user_data",
        )
        instances_pending[0].stop()
        instance = ec2.Instance(instances_pending[0].id)
        assert instance.state["Name"] == "stopped"

        ssm_client = mock.MagicMock
        ssm_client.managed_instances = {}

        from prowler.providers.aws.services.ec2.ec2_service import EC2

        aws_provider = set_mocked_aws_provider(
            [AWS_REGION_EU_WEST_1, AWS_REGION_US_EAST_1]
        )

        with (
            mock.patch(
                "prowler.providers.common.provider.Provider.get_global_provider",
                return_value=aws_provider,
            ),
            mock.patch(
                "prowler.providers.aws.services.ssm.ssm_service.SSM",
                new=ssm_client,
            ),
            mock.patch(
                "prowler.providers.aws.services.ssm.ssm_client.ssm_client",
                new=ssm_client,
            ),
            mock.patch(
                "prowler.providers.aws.services.ec2.ec2_instance_managed_by_ssm.ec2_instance_managed_by_ssm.ec2_client",
                new=EC2(aws_provider),
            ),
        ):
            # Test Check
            from prowler.providers.aws.services.ec2.ec2_instance_managed_by_ssm.ec2_instance_managed_by_ssm import (
                ec2_instance_managed_by_ssm,
            )

            check = ec2_instance_managed_by_ssm()
            result = check.execute()

            assert len(result) == 1
            assert result[0].status == "PASS"
            assert result[0].region == AWS_REGION_US_EAST_1
            assert result[0].resource_tags is None
            assert (
                result[0].status_extended
                == f"EC2 Instance {instance.id} is unmanaged by Systems Manager because it is stopped."
            )

    @mock_aws
    def test_ec2_instance_managed_by_ssm_terminated(self):
        ec2 = resource("ec2", region_name=AWS_REGION_US_EAST_1)
        instances_pending = ec2.create_instances(
            ImageId=EXAMPLE_AMI_ID,
            MinCount=1,
            MaxCount=1,
            UserData="This is some user_data",
        )
        instances_pending[0].terminate()
        instance = ec2.Instance(instances_pending[0].id)
        assert instance.state["Name"] == "terminated"

        ssm_client = mock.MagicMock
        ssm_client.managed_instances = {}

        from prowler.providers.aws.services.ec2.ec2_service import EC2

        aws_provider = set_mocked_aws_provider(
            [AWS_REGION_EU_WEST_1, AWS_REGION_US_EAST_1]
        )

        with (
            mock.patch(
                "prowler.providers.common.provider.Provider.get_global_provider",
                return_value=aws_provider,
            ),
            mock.patch(
                "prowler.providers.aws.services.ssm.ssm_service.SSM",
                new=ssm_client,
            ),
            mock.patch(
                "prowler.providers.aws.services.ssm.ssm_client.ssm_client",
                new=ssm_client,
            ),
            mock.patch(
                "prowler.providers.aws.services.ec2.ec2_instance_managed_by_ssm.ec2_instance_managed_by_ssm.ec2_client",
                new=EC2(aws_provider),
            ),
        ):
            # Test Check
            from prowler.providers.aws.services.ec2.ec2_instance_managed_by_ssm.ec2_instance_managed_by_ssm import (
                ec2_instance_managed_by_ssm,
            )

            check = ec2_instance_managed_by_ssm()
            result = check.execute()

            assert len(result) == 1
            assert result[0].status == "PASS"
            assert result[0].region == AWS_REGION_US_EAST_1
            assert result[0].resource_tags is None
            assert (
                result[0].status_extended
                == f"EC2 Instance {instance.id} is unmanaged by Systems Manager because it is terminated."
            )
