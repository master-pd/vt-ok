"""
AWS Cloud Integration and Auto-Scaling for VT ULTRA PRO
"""

import boto3
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import asyncio

logger = logging.getLogger(__name__)

class AWSScaleManager:
    """AWS cloud scaling and management"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.ec2_client = None
        self.ec2_resource = None
        self.asg_client = None
        self.elb_client = None
        self.cloudwatch_client = None
        self.s3_client = None
        
        self._initialize_clients()
        logger.info(f"AWS Scale Manager initialized for region: {region}")
    
    def _initialize_clients(self):
        """Initialize AWS clients"""
        try:
            self.ec2_client = boto3.client('ec2', region_name=self.region)
            self.ec2_resource = boto3.resource('ec2', region_name=self.region)
            self.asg_client = boto3.client('autoscaling', region_name=self.region)
            self.elb_client = boto3.client('elbv2', region_name=self.region)
            self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.region)
            self.s3_client = boto3.client('s3', region_name=self.region)
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise
    
    async def create_worker_instance(self, instance_type: str = 't3.medium',
                                   image_id: str = 'ami-0c55b159cbfafe1f0',
                                   key_name: str = 'vt-ultra-pro-key',
                                   security_group_ids: List[str] = None,
                                   user_data: str = None) -> Dict[str, Any]:
        """Create a new EC2 worker instance"""
        try:
            if security_group_ids is None:
                security_group_ids = ['sg-0123456789abcdef0']
            
            response = self.ec2_client.run_instances(
                ImageId=image_id,
                InstanceType=instance_type,
                KeyName=key_name,
                SecurityGroupIds=security_group_ids,
                MinCount=1,
                MaxCount=1,
                UserData=user_data,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': 'VT-Ultra-Pro-Worker'},
                            {'Key': 'Project', 'Value': 'VT-Ultra-Pro'},
                            {'Key': 'Environment', 'Value': 'Production'},
                            {'Key': 'CreationTime', 'Value': datetime.now().isoformat()}
                        ]
                    }
                ]
            )
            
            instance = response['Instances'][0]
            instance_id = instance['InstanceId']
            
            logger.info(f"Created EC2 instance: {instance_id}")
            
            return {
                'success': True,
                'instance_id': instance_id,
                'state': instance['State']['Name'],
                'private_ip': instance.get('PrivateIpAddress'),
                'public_ip': instance.get('PublicIpAddress'),
                'instance_type': instance['InstanceType']
            }
            
        except Exception as e:
            logger.error(f"Failed to create EC2 instance: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_auto_scaling_group(self, group_name: str, 
                                      launch_template_id: str,
                                      min_size: int = 1,
                                      max_size: int = 10,
                                      desired_capacity: int = 2,
                                      vpc_zone_identifier: str = None,
                                      target_groups: List[str] = None) -> Dict[str, Any]:
        """Create Auto Scaling Group"""
        try:
            if vpc_zone_identifier is None:
                vpc_zone_identifier = 'subnet-0123456789abcdef0,subnet-0123456789abcdef1'
            
            if target_groups is None:
                target_groups = []
            
            response = self.asg_client.create_auto_scaling_group(
                AutoScalingGroupName=group_name,
                LaunchTemplate={
                    'LaunchTemplateId': launch_template_id,
                    'Version': '$Latest'
                },
                MinSize=min_size,
                MaxSize=max_size,
                DesiredCapacity=desired_capacity,
                VPCZoneIdentifier=vpc_zone_identifier,
                TargetGroupARNs=target_groups,
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'VT-Ultra-Pro',
                        'PropagateAtLaunch': True
                    },
                    {
                        'Key': 'Environment',
                        'Value': 'Production',
                        'PropagateAtLaunch': True
                    }
                ]
            )
            
            logger.info(f"Created Auto Scaling Group: {group_name}")
            
            # Create scaling policies
            await self.create_scaling_policies(group_name)
            
            return {
                'success': True,
                'group_name': group_name,
                'min_size': min_size,
                'max_size': max_size,
                'desired_capacity': desired_capacity
            }
            
        except Exception as e:
            logger.error(f"Failed to create Auto Scaling Group: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_scaling_policies(self, group_name: str):
        """Create scaling policies for Auto Scaling Group"""
        try:
            # Scale-out policy (CPU > 70%)
            self.asg_client.put_scaling_policy(
                AutoScalingGroupName=group_name,
                PolicyName=f'{group_name}-scale-out',
                PolicyType='TargetTrackingScaling',
                TargetTrackingConfiguration={
                    'PredefinedMetricSpecification': {
                        'PredefinedMetricType': 'ASGAverageCPUUtilization'
                    },
                    'TargetValue': 70.0,
                    'ScaleOutCooldown': 60,
                    'ScaleInCooldown': 300
                }
            )
            
            # Scale-in policy (CPU < 30%)
            self.asg_client.put_scaling_policy(
                AutoScalingGroupName=group_name,
                PolicyName=f'{group_name}-scale-in',
                PolicyType='TargetTrackingScaling',
                TargetTrackingConfiguration={
                    'PredefinedMetricSpecification': {
                        'PredefinedMetricType': 'ASGAverageCPUUtilization'
                    },
                    'TargetValue': 30.0,
                    'ScaleOutCooldown': 300,
                    'ScaleInCooldown': 60
                }
            )
            
            logger.info(f"Created scaling policies for {group_name}")
            
        except Exception as e:
            logger.error(f"Failed to create scaling policies: {e}")
    
    async def create_load_balancer(self, name: str, subnets: List[str],
                                 security_groups: List[str]) -> Dict[str, Any]:
        """Create Application Load Balancer"""
        try:
            response = self.elb_client.create_load_balancer(
                Name=name,
                Subnets=subnets,
                SecurityGroups=security_groups,
                Scheme='internet-facing',
                Type='application',
                Tags=[
                    {'Key': 'Project', 'Value': 'VT-Ultra-Pro'},
                    {'Key': 'Environment', 'Value': 'Production'}
                ]
            )
            
            lb = response['LoadBalancers'][0]
            
            # Create target group
            tg_response = self.elb_client.create_target_group(
                Name=f'{name}-tg',
                Protocol='HTTP',
                Port=80,
                VpcId=lb['VpcId'],
                HealthCheckProtocol='HTTP',
                HealthCheckPort='80',
                HealthCheckPath='/health',
                HealthCheckIntervalSeconds=30,
                HealthCheckTimeoutSeconds=5,
                HealthyThresholdCount=2,
                UnhealthyThresholdCount=2,
                TargetType='instance'
            )
            
            target_group = tg_response['TargetGroups'][0]
            
            # Create listener
            self.elb_client.create_listener(
                LoadBalancerArn=lb['LoadBalancerArn'],
                Protocol='HTTP',
                Port=80,
                DefaultActions=[
                    {
                        'Type': 'forward',
                        'TargetGroupArn': target_group['TargetGroupArn']
                    }
                ]
            )
            
            logger.info(f"Created Load Balancer: {lb['DNSName']}")
            
            return {
                'success': True,
                'load_balancer_arn': lb['LoadBalancerArn'],
                'dns_name': lb['DNSName'],
                'target_group_arn': target_group['TargetGroupArn'],
                'vpc_id': lb['VpcId']
            }
            
        except Exception as e:
            logger.error(f"Failed to create Load Balancer: {e}")
            return {'success': False, 'error': str(e)}
    
    async def setup_s3_bucket(self, bucket_name: str) -> Dict[str, Any]:
        """Setup S3 bucket for storage"""
        try:
            # Create bucket
            self.s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': self.region
                }
            )
            
            # Enable versioning
            self.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={
                    'Status': 'Enabled'
                }
            )
            
            # Configure lifecycle rules
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration={
                    'Rules': [
                        {
                            'ID': 'LogsExpiration',
                            'Status': 'Enabled',
                            'Prefix': 'logs/',
                            'Expiration': {'Days': 90},
                            'NoncurrentVersionExpiration': {'NoncurrentDays': 30}
                        },
                        {
                            'ID': 'BackupsTransition',
                            'Status': 'Enabled',
                            'Prefix': 'backups/',
                            'Transitions': [
                                {
                                    'Days': 30,
                                    'StorageClass': 'STANDARD_IA'
                                },
                                {
                                    'Days': 90,
                                    'StorageClass': 'GLACIER'
                                }
                            ]
                        }
                    ]
                }
            )
            
            logger.info(f"Created S3 bucket: {bucket_name}")
            
            return {
                'success': True,
                'bucket_name': bucket_name,
                'region': self.region,
                'url': f'https://{bucket_name}.s3.{self.region}.amazonaws.com/'
            }
            
        except Exception as e:
            logger.error(f"Failed to create S3 bucket: {e}")
            return {'success': False, 'error': str(e)}
    
    async def deploy_cloudformation_stack(self, stack_name: str,
                                        template_body: str) -> Dict[str, Any]:
        """Deploy CloudFormation stack"""
        try:
            import yaml
            
            # Convert YAML to JSON if needed
            try:
                json.loads(template_body)
                template_format = 'JSON'
            except:
                template_dict = yaml.safe_load(template_body)
                template_body = json.dumps(template_dict)
                template_format = 'YAML'
            
            cf_client = boto3.client('cloudformation', region_name=self.region)
            
            response = cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
                Tags=[
                    {'Key': 'Project', 'Value': 'VT-Ultra-Pro'},
                    {'Key': 'Environment', 'Value': 'Production'}
                ],
                OnFailure='ROLLBACK'
            )
            
            logger.info(f"Created CloudFormation stack: {stack_name}")
            
            return {
                'success': True,
                'stack_id': response['StackId'],
                'stack_name': stack_name,
                'template_format': template_format
            }
            
        except Exception as e:
            logger.error(f"Failed to deploy CloudFormation stack: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_cloud_metrics(self, namespace: str = 'AWS/EC2',
                              metric_name: str = 'CPUUtilization',
                              dimensions: List[Dict] = None,
                              period: int = 300,
                              start_time: datetime = None,
                              end_time: datetime = None) -> Dict[str, Any]:
        """Get CloudWatch metrics"""
        try:
            if start_time is None:
                start_time = datetime.utcnow() - timedelta(hours=1)
            if end_time is None:
                end_time = datetime.utcnow()
            
            if dimensions is None:
                dimensions = [{'Name': 'InstanceId', 'Value': 'i-0123456789abcdef0'}]
            
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=['Average', 'Maximum', 'Minimum', 'SampleCount'],
                Unit='Percent'
            )
            
            datapoints = response['Datapoints']
            
            if datapoints:
                # Sort by timestamp
                datapoints.sort(key=lambda x: x['Timestamp'])
                
                return {
                    'success': True,
                    'metric': metric_name,
                    'namespace': namespace,
                    'datapoints': datapoints,
                    'statistics': {
                        'average': sum(d['Average'] for d in datapoints) / len(datapoints),
                        'maximum': max(d['Maximum'] for d in datapoints),
                        'minimum': min(d['Minimum'] for d in datapoints),
                        'sample_count': sum(d['SampleCount'] for d in datapoints)
                    }
                }
            else:
                return {
                    'success': True,
                    'metric': metric_name,
                    'datapoints': [],
                    'message': 'No datapoints available'
                }
            
        except Exception as e:
            logger.error(f"Failed to get CloudWatch metrics: {e}")
            return {'success': False, 'error': str(e)}
    
    async def scale_workers(self, action: str, count: int = 1,
                          instance_ids: List[str] = None) -> Dict[str, Any]:
        """Scale worker instances"""
        try:
            if action == 'start':
                if instance_ids:
                    self.ec2_client.start_instances(InstanceIds=instance_ids)
                    message = f"Started instances: {instance_ids}"
                else:
                    # Start stopped instances with VT-Ultra-Pro tag
                    response = self.ec2_client.describe_instances(
                        Filters=[
                            {'Name': 'tag:Project', 'Values': ['VT-Ultra-Pro']},
                            {'Name': 'instance-state-name', 'Values': ['stopped']}
                        ]
                    )
                    
                    stopped_instances = []
                    for reservation in response['Reservations']:
                        for instance in reservation['Instances']:
                            stopped_instances.append(instance['InstanceId'])
                    
                    if stopped_instances:
                        self.ec2_client.start_instances(InstanceIds=stopped_instances[:count])
                        message = f"Started {min(count, len(stopped_instances))} instances"
                    else:
                        message = "No stopped instances found"
                
            elif action == 'stop':
                if instance_ids:
                    self.ec2_client.stop_instances(InstanceIds=instance_ids)
                    message = f"Stopped instances: {instance_ids}"
                else:
                    # Stop running instances with VT-Ultra-Pro tag
                    response = self.ec2_client.describe_instances(
                        Filters=[
                            {'Name': 'tag:Project', 'Values': ['VT-Ultra-Pro']},
                            {'Name': 'instance-state-name', 'Values': ['running']}
                        ]
                    )
                    
                    running_instances = []
                    for reservation in response['Reservations']:
                        for instance in reservation['Instances']:
                            running_instances.append(instance['InstanceId'])
                    
                    if running_instances:
                        self.ec2_client.stop_instances(InstanceIds=running_instances[:count])
                        message = f"Stopped {min(count, len(running_instances))} instances"
                    else:
                        message = "No running instances found"
            
            elif action == 'terminate':
                if instance_ids:
                    self.ec2_client.terminate_instances(InstanceIds=instance_ids)
                    message = f"Terminated instances: {instance_ids}"
                else:
                    message = "Instance IDs required for termination"
            
            else:
                return {'success': False, 'error': f'Invalid action: {action}'}
            
            logger.info(message)
            return {'success': True, 'message': message}
            
        except Exception as e:
            logger.error(f"Failed to scale workers: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_infrastructure_status(self) -> Dict[str, Any]:
        """Get infrastructure status"""
        try:
            status = {
                'ec2_instances': await self._get_ec2_status(),
                'auto_scaling_groups': await self._get_asg_status(),
                'load_balancers': await self._get_elb_status(),
                's3_buckets': await self._get_s3_status(),
                'cloudwatch_alarms': await self._get_alarm_status(),
                'timestamp': datetime.now().isoformat()
            }
            
            return {'success': True, 'status': status}
            
        except Exception as e:
            logger.error(f"Failed to get infrastructure status: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_ec2_status(self) -> List[Dict]:
        """Get EC2 instances status"""
        try:
            response = self.ec2_client.describe_instances(
                Filters=[
                    {'Name': 'tag:Project', 'Values': ['VT-Ultra-Pro']}
                ]
            )
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'instance_id': instance['InstanceId'],
                        'instance_type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'private_ip': instance.get('PrivateIpAddress'),
                        'public_ip': instance.get('PublicIpAddress'),
                        'launch_time': instance['LaunchTime'].isoformat(),
                        'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    })
            
            return instances
            
        except Exception as e:
            logger.error(f"Failed to get EC2 status: {e}")
            return []
    
    async def _get_asg_status(self) -> List[Dict]:
        """Get Auto Scaling Groups status"""
        try:
            response = self.asg_client.describe_auto_scaling_groups()
            
            asgs = []
            for asg in response['AutoScalingGroups']:
                # Filter for VT-Ultra-Pro groups
                tags = {tag['Key']: tag['Value'] for tag in asg.get('Tags', [])}
                if tags.get('Project') == 'VT-Ultra-Pro':
                    asgs.append({
                        'name': asg['AutoScalingGroupName'],
                        'min_size': asg['MinSize'],
                        'max_size': asg['MaxSize'],
                        'desired_capacity': asg['DesiredCapacity'],
                        'instances': len(asg['Instances']),
                        'health_check_type': asg['HealthCheckType'],
                        'created_time': asg.get('CreatedTime', '').isoformat()
                    })
            
            return asgs
            
        except Exception as e:
            logger.error(f"Failed to get ASG status: {e}")
            return []
    
    async def _get_elb_status(self) -> List[Dict]:
        """Get Load Balancers status"""
        try:
            response = self.elb_client.describe_load_balancers()
            
            load_balancers = []
            for lb in response['LoadBalancers']:
                # Get tags to filter
                tags_response = self.elb_client.describe_tags(
                    ResourceArns=[lb['LoadBalancerArn']]
                )
                
                tags = {}
                for tag_desc in tags_response['TagDescriptions']:
                    for tag in tag_desc['Tags']:
                        tags[tag['Key']] = tag['Value']
                
                if tags.get('Project') == 'VT-Ultra-Pro':
                    load_balancers.append({
                        'name': lb['LoadBalancerName'],
                        'dns_name': lb['DNSName'],
                        'state': lb['State']['Code'],
                        'type': lb['Type'],
                        'scheme': lb['Scheme'],
                        'vpc_id': lb['VpcId']
                    })
            
            return load_balancers
            
        except Exception as e:
            logger.error(f"Failed to get ELB status: {e}")
            return []
    
    async def _get_s3_status(self) -> List[Dict]:
        """Get S3 buckets status"""
        try:
            response = self.s3_client.list_buckets()
            
            buckets = []
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                
                # Check if it's our bucket
                try:
                    tags_response = self.s3_client.get_bucket_tagging(Bucket=bucket_name)
                    tags = {tag['Key']: tag['Value'] for tag in tags_response['TagSet']}
                    
                    if tags.get('Project') == 'VT-Ultra-Pro':
                        # Get bucket size
                        try:
                            metrics = self.cloudwatch_client.get_metric_statistics(
                                Namespace='AWS/S3',
                                MetricName='BucketSizeBytes',
                                Dimensions=[
                                    {'Name': 'BucketName', 'Value': bucket_name},
                                    {'Name': 'StorageType', 'Value': 'StandardStorage'}
                                ],
                                StartTime=datetime.utcnow() - timedelta(days=1),
                                EndTime=datetime.utcnow(),
                                Period=86400,
                                Statistics=['Average']
                            )
                            
                            size_bytes = metrics['Datapoints'][0]['Average'] if metrics['Datapoints'] else 0
                        except:
                            size_bytes = 0
                        
                        buckets.append({
                            'name': bucket_name,
                            'creation_date': bucket['CreationDate'].isoformat(),
                            'size_bytes': size_bytes,
                            'size_human': self._bytes_to_human(size_bytes),
                            'tags': tags
                        })
                except:
                    continue
            
            return buckets
            
        except Exception as e:
            logger.error(f"Failed to get S3 status: {e}")
            return []
    
    async def _get_alarm_status(self) -> List[Dict]:
        """Get CloudWatch alarms status"""
        try:
            response = self.cloudwatch_client.describe_alarms()
            
            alarms = []
            for alarm in response['MetricAlarms']:
                # Filter for VT-Ultra-Pro alarms
                if 'VT-Ultra-Pro' in alarm.get('AlarmName', ''):
                    alarms.append({
                        'name': alarm['AlarmName'],
                        'state': alarm['StateValue'],
                        'metric': alarm['MetricName'],
                        'threshold': alarm['Threshold'],
                        'comparison': alarm['ComparisonOperator'],
                        'period': alarm['Period'],
                        'evaluation_periods': alarm['EvaluationPeriods']
                    })
            
            return alarms
            
        except Exception as e:
            logger.error(f"Failed to get alarm status: {e}")
            return []
    
    def _bytes_to_human(self, bytes_size: float) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"