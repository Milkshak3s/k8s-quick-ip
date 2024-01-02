import asyncio
import datetime
import os
import random
import string

import kopf
import kubernetes.client.rest
import yaml


def check_spec_fields(field_names, spec):
    for name in field_names:
        spec_value = spec.get(name)
        if spec_value is None:
            raise kopf.HandlerFatalError(f"{name} must be set. Got {spec_value!r}.")
        

def generate_client_deploy_name(name):
    return f"frpc-{name}"


@kopf.on.create('experimental.milkshakes.cloud', 'v1', 'frpgcpremotes')
def create_fn(meta, spec, namespace, logger, body, **kwargs):
    fields = ['dns_a_name', 'dns_base_domain', 'dns_zone', 'frp_local_service_addr', 'frp_local_service_port', 'frp_remote_port', 'frp_server_port', 'gcp_project_id', 'gcp_service_account_secret']
    check_spec_fields(fields, spec)

    remote_job_name = f"deployremote-{meta.get('name')}"
    client_deploy_name = generate_client_deploy_name(meta.get('name'))

    gcp_project_id = spec.get('gcp_project_id')
    dns_a_name = spec.get('dns_a_name')
    dns_zone = spec.get('dns_zone')
    dns_base_domain = spec.get('dns_base_domain')
    frp_server_port = spec.get('frp_server_port')
    gcp_service_account_secret = spec.get('gcp_service_account_secret')


    path = os.path.join(os.path.dirname(__file__), 'remote-job.yaml')
    tmpl = open(path, 'rt').read()
    text = tmpl.format(name=remote_job_name, gcp_project_id=gcp_project_id, dns_a_name=dns_a_name, dns_zone=dns_zone, dns_base_domain=dns_base_domain, frp_server_port=frp_server_port, gcp_service_account_secret=gcp_service_account_secret, delete_not_create="false")
    data = yaml.load(text, yaml.Loader)

    kopf.adopt(data, owner=body)

    # run job to deploy remote GCP resources
    batch_api = kubernetes.client.BatchV1Api()
    obj = batch_api.create_namespaced_job(
        namespace=namespace,
        body=data,
    )

    logger.info(f"FrpGCPRemote deploy job is created: {obj}")

    dns_full_name = f"{dns_a_name}.{dns_zone}.{dns_base_domain}"
    frp_local_service_addr = spec.get('frp_local_service_addr')
    frp_local_service_port = spec.get('frp_local_service_port')
    frp_remote_port = spec.get('frp_remote_port')

    path = os.path.join(os.path.dirname(__file__), 'client-deploy.yaml')
    tmpl = open(path, 'rt').read()
    text = tmpl.format(name=client_deploy_name, frp_server_addr=dns_full_name, frp_server_port=frp_server_port, frp_local_service_addr=frp_local_service_addr, frp_local_service_port=frp_local_service_port, frp_remote_port=frp_remote_port)
    data = yaml.load(text, yaml.Loader)

    kopf.adopt(data, owner=body)

    # run local client deployment
    apps_api = kubernetes.client.AppsV1Api()
    obj = apps_api.create_namespaced_deployment(
        namespace=namespace,
        body=data,
    )

    return {'FrpGCPRemote-job-name': obj.metadata.name}


@kopf.on.delete('experimental.milkshakes.cloud', 'v1', 'frpgcpremotes')
def delete_fn(body, meta, spec, status, **kwargs):
    # run job to delete remote GCP resources
    remote_job_name = f"deleteremote-{meta.get('name')}"
    gcp_project_id = spec.get('gcp_project_id')
    dns_a_name = spec.get('dns_a_name')
    dns_zone = spec.get('dns_zone')
    dns_base_domain = spec.get('dns_base_domain')
    frp_server_port = spec.get('frp_server_port')
    gcp_service_account_secret = spec.get('gcp_service_account_secret')


    path = os.path.join(os.path.dirname(__file__), 'remote-job.yaml')
    tmpl = open(path, 'rt').read()
    text = tmpl.format(name=remote_job_name, gcp_project_id=gcp_project_id, dns_a_name=dns_a_name, dns_zone=dns_zone, dns_base_domain=dns_base_domain, frp_server_port=frp_server_port, gcp_service_account_secret=gcp_service_account_secret, delete_not_create="true")
    data = yaml.load(text, yaml.Loader)

    # kopf.adopt(data, owner=body)

    # run job to deploy remote GCP resources
    namespace = meta.get('namespace')
    batch_api = kubernetes.client.BatchV1Api()
    obj = batch_api.create_namespaced_job(
        namespace=namespace,
        body=data,
    )

    # delete frpc client deployment
    apps_api = kubernetes.client.AppsV1Api()
    apps_api.delete_namespaced_deployment(name=generate_client_deploy_name(meta.get('name')), namespace=namespace)

    return {'FrpGCPRemote-delete-job-name': obj.metadata.name}


@kopf.on.create('experimental.milkshakes.cloud', 'v1', 'frpclients')
def create_frpc_fn(meta, spec, namespace, logger, body, **kwargs):
    fields = ['frp_local_service_addr', 'frp_local_service_port', 'frp_remote_port', 'frp_server_port', 'frp_server_addr']
    check_spec_fields(fields, spec)

    client_deploy_name = generate_client_deploy_name(meta.get('name'))

    frp_server_addr = spec.get('frp_server_addr')
    frp_server_port = spec.get('frp_server_port')
    frp_local_service_addr = spec.get('frp_local_service_addr')
    frp_local_service_port = spec.get('frp_local_service_port')
    frp_remote_port = spec.get('frp_remote_port')

    path = os.path.join(os.path.dirname(__file__), 'client-deploy.yaml')
    tmpl = open(path, 'rt').read()
    text = tmpl.format(name=client_deploy_name, frp_server_addr=frp_server_addr, frp_server_port=frp_server_port, frp_local_service_addr=frp_local_service_addr, frp_local_service_port=frp_local_service_port, frp_remote_port=frp_remote_port)
    data = yaml.load(text, yaml.Loader)

    kopf.adopt(data, owner=body)

    # run local client deployment
    apps_api = kubernetes.client.AppsV1Api()
    obj = apps_api.create_namespaced_deployment(
        namespace=namespace,
        body=data,
    )

    return {'FrpClient-name': obj.metadata.name}
