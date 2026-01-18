#!/usr/bin/env python3
"""
Fetch NBA data from multiple endpoints and upload to S3.

This script reads a configuration file to determine which endpoints to fetch,
then uploads each dataset to S3 with endpoint-specific paths.
"""

import json
import os
import importlib
from datetime import datetime, timezone
from pathlib import Path

import boto3


def load_config():
    """Load endpoint configuration from JSON file."""
    config_path = Path(__file__).parent / 'endpoints_config.json'
    with open(config_path, 'r') as f:
        return json.load(f)


def fetch_endpoint_data(endpoint_config):
    """Fetch data from a configured endpoint."""
    endpoint_name = endpoint_config['name']
    module_path = endpoint_config['module']
    class_name = endpoint_config['class']
    
    print(f"\nFetching {endpoint_name} data...")
    
    # Dynamically import the endpoint module and class
    module = importlib.import_module(module_path)
    endpoint_class = getattr(module, class_name)
    
    # Instantiate and fetch data
    endpoint_instance = endpoint_class()
    data = endpoint_instance.get_dict()
    
    # Add metadata
    data['metadata'] = {
        'endpoint': endpoint_name,
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'source': f"{module_path}.{class_name}"
    }
    
    return data


def upload_to_s3(data, endpoint_name, bucket_name):
    """Upload data to S3 bucket with endpoint-specific path structure."""
    s3_client = boto3.client('s3')
    
    # Create S3 key: nba-data/{endpoint}/{date}/{timestamp}.json
    now = datetime.now(timezone.utc)
    date_str = now.strftime('%Y-%m-%d')
    timestamp_str = now.strftime('%H-%M-%S')
    s3_key = f"nba-data/{endpoint_name}/{date_str}/{timestamp_str}.json"
    
    # Convert to JSON string
    json_data = json.dumps(data, indent=2)
    
    print(f"Uploading to s3://{bucket_name}/{s3_key}")
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json_data,
        ContentType='application/json'
    )
    
    print(f"✓ Successfully uploaded {len(json_data)} bytes to S3")
    return s3_key


def main():
    """Main execution function."""
    # Get S3 bucket name from environment variable
    bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
    if not bucket_name:
        raise ValueError("AWS_S3_BUCKET_NAME environment variable not set")
    
    print(f"Target S3 bucket: {bucket_name}")
    
    # Load endpoint configuration
    config = load_config()
    enabled_endpoints = [ep for ep in config['endpoints'] if ep.get('enabled', True)]
    
    print(f"\n=== Processing {len(enabled_endpoints)} endpoint(s) ===")
    
    results = []
    for endpoint_config in enabled_endpoints:
        try:
            # Fetch data
            data = fetch_endpoint_data(endpoint_config)
            
            # Upload to S3
            s3_key = upload_to_s3(data, endpoint_config['name'], bucket_name)
            
            results.append({
                'endpoint': endpoint_config['name'],
                'status': 'success',
                's3_key': s3_key
            })
        except Exception as e:
            print(f"✗ Error processing {endpoint_config['name']}: {str(e)}")
            results.append({
                'endpoint': endpoint_config['name'],
                'status': 'failed',
                'error': str(e)
            })
    
    # Summary
    print(f"\n=== Upload Complete ===")
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    print(f"Successful: {successful}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    
    for result in results:
        if result['status'] == 'success':
            print(f"✓ {result['endpoint']}: s3://{bucket_name}/{result['s3_key']}")
        else:
            print(f"✗ {result['endpoint']}: {result['error']}")
    
    # Exit with error if any failed
    if failed > 0:
        exit(1)


if __name__ == '__main__':
    main()
