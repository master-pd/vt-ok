"""
Google Cloud Platform Integration for VT ULTRA PRO
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from google.cloud import compute_v1
from google.cloud import storage
from google.cloud import monitoring_v3
from google.api_core.exceptions import GoogleAPICallError

logger = logging.getLogger(__name__)

class GCPWorkerManager:
    """GCP cloud integration and worker management"""
    
    def __init__(self, project_id: str, zone: str = 'us-central1-a'):
        self.project_id = project_id
        self.zone = zone
        self.region = '-'.join(zone.split('-')[:-1])
        
        # Initialize GCP clients
        self.compute_client = None
        self.storage_client = None
        self.monitoring_client = None
        
        self._initialize_clients()
        logger.info(f"GCP Worker Manager initialized for project: {project_id}")
    
    def _initialize_clients(self):
        """Initialize GCP clients"""
        try:
            self.compute_client = compute_v1.InstancesClient()
            self.storage_client = storage.Client(project=self.project_id)
            self.monitoring_client = monitoring_v3.MetricServiceClient()
            
        except Exception as e:
            logger.error(f"Failed to initialize GCP clients: {e}")
            raise
    
    async def create_vm_instance(self, instance_name: str,
                               machine_type: str = 'e2-medium',
                               image_project: str = 'ubuntu-os-cloud',
                               image_family: str = 'ubuntu-2204-lts',
                               disk_size_gb: int = 50,
                               network: str = 'global/networks/default',
                               startup_script: str = None) -> Dict[str, Any]:
        """Create a new VM instance"""
        try:
            # Get the latest image
            image_client = compute_v1.ImagesClient()
            image = image_client.get_from_family(
                project=image_project,
                family=image_family
            )
            
            # Configure the instance
            instance = compute_v1.Instance()
            instance.name = instance_name
            instance.machine_type = f'zones/{self.zone}/machineTypes/{machine_type}'
            
            # Configure disk
            disk = compute_v1.AttachedDisk()
            initialize_params = compute_v1.AttachedDiskInitializeParams()
            initialize_params.source_image = image.self_link
            initialize_params.disk_size_gb = disk_size_gb
            initialize_params.disk_type = f'zones/{self.zone}/diskTypes/pd-standard'
            disk.initialize_params = initialize_params
            disk.boot = True
            disk.auto_delete = True
            
            instance.disks = [disk]
            
            # Configure network
            network_interface = compute_v1.NetworkInterface()
            network_interface.name = network
            network_interface.access_configs = [
                compute_v1.AccessConfig(
                    name='External NAT',
                    type_='ONE_TO_ONE_NAT'
                )
            ]
            instance.network_interfaces = [network_interface]
            
            # Add metadata (startup script, labels)
            instance.metadata = compute_v1.Metadata()
            
            if startup_script:
                instance.metadata.items = [
                    compute_v1.Items(
                        key='startup-script',
                        value=startup_script
                    )
                ]
            
            # Add labels
            instance.labels = {
                'project': 'vt-ultra-pro',
                'environment': 'production',
                'created': datetime.now().strftime('%Y%m%d')
            }
            
            # Create the instance
            operation = self.compute_client.insert(
                project=self.project_id,
                zone=self.zone,
                instance_resource=instance
            )
            
            # Wait for operation to complete
            operation.result()
            
            # Get the created instance
            created_instance = self.compute_client.get(
                project=self.project_id,
                zone=self.zone,
                instance=instance_name
            )
            
            logger.info(f"Created VM instance: {instance_name}")
            
            return {
                'success': True,
                'instance_name': instance_name,
                'status': created_instance.status,
                'internal_ip': created_instance.network_interfaces[0].network_i_p,
                'external_ip': created_instance.network_interfaces[0].access_configs[0].nat_i_p,
                'machine_type': machine_type,
                'creation_timestamp': created_instance.creation_timestamp
            }
            
        except GoogleAPICallError as e:
            logger.error(f"Failed to create VM instance: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error creating VM instance: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_instance_template(self, template_name: str,
                                     machine_type: str = 'e2-medium',
                                     image_project: str = 'ubuntu-os-cloud',
                                     image_family: str = 'ubuntu-2204-lts',
                                     startup_script: str = None) -> Dict[str, Any]:
        """Create instance template for managed instance groups"""
        try:
            template_client = compute_v1.InstanceTemplatesClient()
            
            # Configure the template
            template = compute_v1.InstanceTemplate()
            template.name = template_name
            
            # Properties
            properties = compute_v1.InstanceProperties()
            properties.machine_type = machine_type
            
            # Disk configuration
            disk = compute_v1.AttachedDisk()
            initialize_params = compute_v1.AttachedDiskInitializeParams()
            
            image_client = compute_v1.ImagesClient()
            image = image_client.get_from_family(
                project=image_project,
                family=image_family
            )
            
            initialize_params.source_image = image.self_link
            initialize_params.disk_size_gb = 50
            initialize_params.disk_type = 'pd-standard'
            disk.initialize_params = initialize_params
            disk.boot = True
            disk.auto_delete = True
            
            properties.disks = [disk]
            
            # Network configuration
            network_interface = compute_v1.NetworkInterface()
            network_interface.name = 'global/networks/default'
            network_interface.access_configs = [
                compute_v1.AccessConfig(
                    name='External NAT',
                    type_='ONE_TO_ONE_NAT'
                )
            ]
            properties.network_interfaces = [network_interface]
            
            # Metadata
            if startup_script:
                properties.metadata = compute_v1.Metadata()
                properties.metadata.items = [
                    compute_v1.Items(
                        key='startup-script',
                        value=startup_script
                    )
                ]
            
            # Labels
            properties.labels = {
                'project': 'vt-ultra-pro',
                'environment': 'production'
            }
            
            # Tags
            properties.tags = compute_v1.Tags()
            properties.tags.items = ['vt-ultra-pro-worker']
            
            template.properties = properties
            
            # Create the template
            operation = template_client.insert(
                project=self.project_id,
                instance_template_resource=template
            )
            
            operation.result()
            
            logger.info(f"Created instance template: {template_name}")
            
            return {
                'success': True,
                'template_name': template_name,
                'machine_type': machine_type,
                'image_family': image_family
            }
            
        except GoogleAPICallError as e:
            logger.error(f"Failed to create instance template: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_managed_instance_group(self, group_name: str,
                                          template_name: str,
                                          size: int = 2,
                                          autoscaling: bool = True) -> Dict[str, Any]:
        """Create managed instance group"""
        try:
            mig_client = compute_v1.InstanceGroupManagersClient()
            
            # Create the managed instance group
            mig = compute_v1.InstanceGroupManager()
            mig.name = group_name
            mig.base_instance_name = f'{group_name}-instance'
            mig.target_size = size
            
            # Set instance template
            mig.instance_template = (
                f'projects/{self.project_id}/global/instanceTemplates/{template_name}'
            )
            
            # Configure autohealing
            auto_healing_policies = compute_v1.InstanceGroupManagerAutoHealingPolicy()
            auto_healing_policies.health_check = (
                f'projects/{self.project_id}/global/healthChecks/vt-ultra-pro-health-check'
            )
            auto_healing_policies.initial_delay_sec = 300
            mig.auto_healing_policies = [auto_healing_policies]
            
            # Create the MIG
            operation = mig_client.insert(
                project=self.project_id,
                zone=self.zone,
                instance_group_manager_resource=mig
            )
            
            operation.result()
            
            # Configure autoscaling if enabled
            if autoscaling:
                await self.configure_autoscaling(group_name)
            
            logger.info(f"Created managed instance group: {group_name}")
            
            return {
                'success': True,
                'group_name': group_name,
                'size': size,
                'template': template_name,
                'autoscaling': autoscaling
            }
            
        except GoogleAPICallError as e:
            logger.error(f"Failed to create MIG: {e}")
            return {'success': False, 'error': str(e)}
    
    async def configure_autoscaling(self, group_name: str):
        """Configure autoscaling for instance group"""
        try:
            autoscaler_client = compute_v1.AutoscalersClient()
            
            autoscaler = compute_v1.Autoscaler()
            autoscaler.name = f'{group_name}-autoscaler'
            autoscaler.target = (
                f'projects/{self.project_id}/zones/{self.zone}/instanceGroupManagers/{group_name}'
            )
            
            # Autoscaling policy
            autoscaler.autoscaling_policy = compute_v1.AutoscalingPolicy()
            autoscaler.autoscaling_policy.min_num_replicas = 1
            autoscaler.autoscaling_policy.max_num_replicas = 10
            autoscaler.autoscaling_policy.cool_down_period_sec = 60
            
            # CPU utilization target
            autoscaler.autoscaling_policy.cpu_utilization = compute_v1.AutoscalingPolicyCpuUtilization()
            autoscaler.autoscaling_policy.cpu_utilization.utilization_target = 0.7
            
            # Create autoscaler
            operation = autoscaler_client.insert(
                project=self.project_id,
                zone=self.zone,
                autoscaler_resource=autoscaler
            )
            
            operation.result()
            logger.info(f"Configured autoscaling for {group_name}")
            
        except GoogleAPICallError as e:
            logger.error(f"Failed to configure autoscaling: {e}")
    
    async def create_cloud_storage_bucket(self, bucket_name: str,
                                        location: str = 'US',
                                        versioning: bool = True) -> Dict[str, Any]:
        """Create Cloud Storage bucket"""
        try:
            bucket = self.storage_client.bucket(bucket_name)
            
            if not bucket.exists():
                bucket = self.storage_client.create_bucket(
                    bucket,
                    location=location
                )
            
            # Configure versioning
            if versioning:
                bucket.versioning_enabled = True
                bucket.patch()
            
            # Add lifecycle rules
            lifecycle_rules = [
                {
                    'action': {'type': 'Delete'},
                    'condition': {'age': 90}  # Delete after 90 days
                },
                {
                    'action': {'type': 'SetStorageClass', 'storageClass': 'NEARLINE'},
                    'condition': {'age': 30}  # Archive to Nearline after 30 days
                }
            ]
            
            bucket.lifecycle_rules = lifecycle_rules
            bucket.patch()
            
            logger.info(f"Created Cloud Storage bucket: {bucket_name}")
            
            return {
                'success': True,
                'bucket_name': bucket_name,
                'location': location,
                'url': f'https://storage.googleapis.com/{bucket_name}/'
            }
            
        except Exception as e:
            logger.error(f"Failed to create storage bucket: {e}")
            return {'success': False, 'error': str(e)}
    
    async def deploy_cloud_function(self, function_name: str,
                                  runtime: str = 'python39',
                                  entry_point: str = 'main',
                                  source_code_path: str = None,
                                  trigger_http: bool = True) -> Dict[str, Any]:
        """Deploy Cloud Function"""
        try:
            from google.cloud import functions_v1
            
            functions_client = functions_v1.CloudFunctionsServiceClient()
            
            # Prepare function configuration
            function = functions_v1.CloudFunction()
            function.name = f'projects/{self.project_id}/locations/{self.region}/functions/{function_name}'
            function.runtime = runtime
            function.entry_point = entry_point
            function.available_memory_mb = 256
            function.timeout = 60
            
            # Configure source
            if source_code_path:
                # Upload from local source
                pass
            else:
                # Use inline source code
                function.source_archive_url = (
                    f'gs://{self.project_id}-functions/{function_name}.zip'
                )
            
            # Configure trigger
            if trigger_http:
                function.https_trigger = functions_v1.HttpsTrigger()
            else:
                # Configure other triggers (Pub/Sub, Storage, etc.)
                pass
            
            # Deploy the function
            operation = functions_client.create_function(
                location=f'projects/{self.project_id}/locations/{self.region}',
                function=function
            )
            
            # Wait for deployment
            response = operation.result()
            
            logger.info(f"Deployed Cloud Function: {function_name}")
            
            return {
                'success': True,
                'function_name': function_name,
                'status': response.status,
                'https_trigger_url': response.https_trigger.url if trigger_http else None
            }
            
        except Exception as e:
            logger.error(f"Failed to deploy Cloud Function: {e}")
            return {'success': False, 'error': str(e)}
    
    async def setup_monitoring_dashboard(self, dashboard_name: str) -> Dict[str, Any]:
        """Setup Cloud Monitoring dashboard"""
        try:
            dashboard_client = monitoring_v3.DashboardsClient()
            
            # Create dashboard with metrics
            dashboard = {
                'display_name': dashboard_name,
                'grid_layout': {
                    'columns': '2',
                    'widgets': [
                        {
                            'title': 'CPU Utilization',
                            'xy_chart': {
                                'data_sets': [{
                                    'time_series_query': {
                                        'time_series_filter': {
                                            'filter': 'metric.type="compute.googleapis.com/instance/cpu/utilization"',
                                            'aggregation': {
                                                'alignment_period': '60s',
                                                'per_series_aligner': 'ALIGN_MEAN'
                                            }
                                        }
                                    }
                                }]
                            }
                        },
                        {
                            'title': 'Memory Usage',
                            'xy_chart': {
                                'data_sets': [{
                                    'time_series_query': {
                                        'time_series_filter': {
                                            'filter': 'metric.type="agent.googleapis.com/memory/percent_used"',
                                            'aggregation': {
                                                'alignment_period': '60s',
                                                'per_series_aligner': 'ALIGN_MEAN'
                                            }
                                        }
                                    }
                                }]
                            }
                        },
                        {
                            'title': 'Network Traffic',
                            'xy_chart': {
                                'data_sets': [{
                                    'time_series_query': {
                                        'time_series_filter': {
                                            'filter': 'metric.type="compute.googleapis.com/instance/network/sent_bytes_count"',
                                            'aggregation': {
                                                'alignment_period': '60s',
                                                'per_series_aligner': 'ALIGN_RATE'
                                            }
                                        }
                                    }
                                }]
                            }
                        },
                        {
                            'title': 'Disk Operations',
                            'xy_chart': {
                                'data_sets': [{
                                    'time_series_query': {
                                        'time_series_filter': {
                                            'filter': 'metric.type="compute.googleapis.com/instance/disk/write_bytes_count"',
                                            'aggregation': {
                                                'alignment_period': '60s',
                                                'per_series_aligner': 'ALIGN_RATE'
                                            }
                                        }
                                    }
                                }]
                            }
                        }
                    ]
                }
            }
            
            # Create the dashboard
            request = monitoring_v3.CreateDashboardRequest(
                parent=f'projects/{self.project_id}',
                dashboard=dashboard
            )
            
            created_dashboard = dashboard_client.create_dashboard(request)
            
            logger.info(f"Created monitoring dashboard: {dashboard_name}")
            
            return {
                'success': True,
                'dashboard_name': dashboard_name,
                'dashboard_id': created_dashboard.name.split('/')[-1]
            }
            
        except Exception as e:
            logger.error(f"Failed to create monitoring dashboard: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_gcp_metrics(self, metric_type: str,
                            filter_labels: Dict = None,
                            minutes: int = 60) -> Dict[str, Any]:
        """Get GCP monitoring metrics"""
        try:
            project_name = f'projects/{self.project_id}'
            
            # Build filter
            filter_str = f'resource.type="gce_instance" AND metric.type="{metric_type}"'
            
            if filter_labels:
                for key, value in filter_labels.items():
                    filter_str += f' AND resource.labels.{key}="{value}"'
            
            # Set time interval
            now = datetime.utcnow()
            start_time = now - timedelta(minutes=minutes)
            
            interval = monitoring_v3.TimeInterval({
                'end_time': now,
                'start_time': start_time
            })
            
            # Query metrics
            results = self.monitoring_client.list_time_series(
                name=project_name,
                filter=filter_str,
                interval=interval,
                view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
            )
            
            time_series_data = []
            for series in results:
                points = []
                for point in series.points:
                    points.append({
                        'timestamp': point.interval.end_time.isoformat(),
                        'value': point.value.double_value or point.value.int64_value
                    })
                
                time_series_data.append({
                    'metric': series.metric.type,
                    'resource': series.resource.type,
                    'points': points
                })
            
            return {
                'success': True,
                'metric_type': metric_type,
                'time_series': time_series_data,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': now.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get GCP metrics: {e}")
            return {'success': False, 'error': str(e)}
    
    async def manage_worker_instances(self, action: str, 
                                    instance_names: List[str] = None,
                                    group_name: str = None) -> Dict[str, Any]:
        """Manage worker instances"""
        try:
            if action == 'start':
                if instance_names:
                    for instance_name in instance_names:
                        operation = self.compute_client.start(
                            project=self.project_id,
                            zone=self.zone,
                            instance=instance_name
                        )
                        operation.result()
                    message = f"Started instances: {instance_names}"
                elif group_name:
                    # Start all instances in group
                    mig_client = compute_v1.InstanceGroupManagersClient()
                    operation = mig_client.resize(
                        project=self.project_id,
                        zone=self.zone,
                        instance_group_manager=group_name,
                        size=2  # Default size
                    )
                    operation.result()
                    message = f"Started instance group: {group_name}"
                else:
                    message = "Specify instance names or group name"
            
            elif action == 'stop':
                if instance_names:
                    for instance_name in instance_names:
                        operation = self.compute_client.stop(
                            project=self.project_id,
                            zone=self.zone,
                            instance=instance_name
                        )
                        operation.result()
                    message = f"Stopped instances: {instance_names}"
                elif group_name:
                    # Stop all instances in group
                    mig_client = compute_v1.InstanceGroupManagersClient()
                    operation = mig_client.resize(
                        project=self.project_id,
                        zone=self.zone,
                        instance_group_manager=group_name,
                        size=0
                    )
                    operation.result()
                    message = f"Stopped instance group: {group_name}"
                else:
                    message = "Specify instance names or group name"
            
            elif action == 'delete':
                if instance_names:
                    for instance_name in instance_names:
                        operation = self.compute_client.delete(
                            project=self.project_id,
                            zone=self.zone,
                            instance=instance_name
                        )
                        operation.result()
                    message = f"Deleted instances: {instance_names}"
                else:
                    message = "Instance names required for deletion"
            
            else:
                return {'success': False, 'error': f'Invalid action: {action}'}
            
            logger.info(message)
            return {'success': True, 'message': message}
            
        except Exception as e:
            logger.error(f"Failed to manage worker instances: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_gcp_infrastructure_status(self) -> Dict[str, Any]:
        """Get GCP infrastructure status"""
        try:
            status = {
                'compute_instances': await self._get_compute_status(),
                'instance_groups': await self._get_instance_groups_status(),
                'storage_buckets': await self._get_storage_status(),
                'cloud_functions': await self._get_functions_status(),
                'timestamp': datetime.now().isoformat()
            }
            
            return {'success': True, 'status': status}
            
        except Exception as e:
            logger.error(f"Failed to get GCP infrastructure status: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_compute_status(self) -> List[Dict]:
        """Get Compute Engine instances status"""
        try:
            instances = self.compute_client.list(
                project=self.project_id,
                zone=self.zone
            )
            
            instance_list = []
            for instance in instances:
                # Filter for VT-Ultra-Pro instances
                if 'vt-ultra-pro' in instance.labels.get('project', ''):
                    instance_list.append({
                        'name': instance.name,
                        'status': instance.status,
                        'machine_type': instance.machine_type.split('/')[-1],
                        'internal_ip': instance.network_interfaces[0].network_i_p,
                        'external_ip': instance.network_interfaces[0].access_configs[0].nat_i_p if instance.network_interfaces[0].access_configs else None,
                        'creation_timestamp': instance.creation_timestamp,
                        'labels': dict(instance.labels)
                    })
            
            return instance_list
            
        except Exception as e:
            logger.error(f"Failed to get compute status: {e}")
            return []
    
    async def _get_instance_groups_status(self) -> List[Dict]:
        """Get instance groups status"""
        try:
            mig_client = compute_v1.InstanceGroupManagersClient()
            groups = mig_client.list(
                project=self.project_id,
                zone=self.zone
            )
            
            group_list = []
            for group in groups:
                # Filter for VT-Ultra-Pro groups
                if 'vt-ultra-pro' in group.name:
                    group_list.append({
                        'name': group.name,
                        'base_instance_name': group.base_instance_name,
                        'target_size': group.target_size,
                        'current_size': group.current_actions.none if hasattr(group, 'current_actions') else 0,
                        'status': 'ACTIVE' if group.status.is_stable else 'UPDATING'
                    })
            
            return group_list
            
        except Exception as e:
            logger.error(f"Failed to get instance groups status: {e}")
            return []
    
    async def _get_storage_status(self) -> List[Dict]:
        """Get Cloud Storage status"""
        try:
            buckets = list(self.storage_client.list_buckets())
            
            bucket_list = []
            for bucket in buckets:
                # Check labels or name for VT-Ultra-Pro
                if 'vt-ultra-pro' in bucket.name.lower():
                    try:
                        size = sum(blob.size for blob in bucket.list_blobs())
                    except:
                        size = 0
                    
                    bucket_list.append({
                        'name': bucket.name,
                        'location': bucket.location,
                        'storage_class': bucket.storage_class,
                        'size_bytes': size,
                        'size_human': self._bytes_to_human(size),
                        'created': bucket.time_created.isoformat()
                    })
            
            return bucket_list
            
        except Exception as e:
            logger.error(f"Failed to get storage status: {e}")
            return []
    
    async def _get_functions_status(self) -> List[Dict]:
        """Get Cloud Functions status"""
        try:
            from google.cloud import functions_v1
            functions_client = functions_v1.CloudFunctionsServiceClient()
            
            functions = functions_client.list_functions(
                parent=f'projects/{self.project_id}/locations/{self.region}'
            )
            
            function_list = []
            for function in functions:
                if 'vt-ultra-pro' in function.name.lower():
                    function_list.append({
                        'name': function.name.split('/')[-1],
                        'status': function.status.name,
                        'runtime': function.runtime,
                        'entry_point': function.entry_point,
                        'trigger': 'HTTP' if function.https_trigger else 'Other',
                        'update_time': function.update_time.isoformat()
                    })
            
            return function_list
            
        except Exception as e:
            logger.error(f"Failed to get functions status: {e}")
            return []
    
    def _bytes_to_human(self, bytes_size: float) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"