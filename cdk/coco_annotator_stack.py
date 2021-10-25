from aws_cdk import core as cdk

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam


class CocoAnnotatorStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 bucket
        bucket = s3.Bucket(self, "coco-annotator-bucket")

        # Networking
        vpc = ec2.Vpc(self, "coco-annotator-vpc")
        security_group = ec2.SecurityGroup(self, "coco-annotator-sg",
            vpc=vpc,
            description="Allow ssh access to ec2 instances, allow internet access",
            allow_all_outbound=True
        )
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "allow ssh access from the world")

        # Machine OS
        amzn_linux = ec2.MachineImage.latest_amazon_linux()

        # Instance
        instance = ec2.Instance(self, "Instance",
    # Showing the most complex setup, if you have simpler requirements
    # you can use `CloudFormationInit.fromElements()`.
    init=ec2.CloudFormationInit.from_config_sets(
                config_sets={
                    # Applies the configs below in this order
                    "default": ["yumPreinstall", "config"]
                },
                configs={
                    "yum_preinstall": ec2.InitConfig([
                        # Install an Amazon Linux package using yum
                        ec2.InitPackage.yum("git")
                    ]),
                    "config": ec2.InitConfig([
                        # Create a JSON file from tokens (can also create other files)
                        ec2.InitFile.from_object("/etc/stack.json", {
                            "stack_id": self.stack_id,
                            "stack_name": self.stack_name,
                            "region": self.region
                        }),

                        # Create a group and user
                        ec2.InitGroup.from_name("my-group"),
                        ec2.InitUser.from_name("my-user"),

                        # Install an RPM from the internet
                        ec2.InitPackage.rpm("http://mirrors.ukfast.co.uk/sites/dl.fedoraproject.org/pub/epel/8/Everything/x86_64/Packages/r/rubygem-git-1.5.0-2.el8.noarch.rpm")
                    ])
                }
            ),
            init_options=ec2.ApplyCloudFormationInitOptions(
                config_sets=["default"],
                timeout=cdk.Duration.minutes(30),
            ),
            instance_type=ec2.InstanceType("t2.medium"),
            machine_image = amzn_linux, 
            vpc = vpc,

        )

        role = iam.Role(self, "coco-annotator-role",
            assumed_by=iam.AccountRootPrincipal()
        )
        volume = ec2.Volume(self, "Volume",
            availability_zone=self.region,
            size=cdk.Size.gibibytes(30)
        )
        volume.grant_attach_volume(role, [instance])




                
