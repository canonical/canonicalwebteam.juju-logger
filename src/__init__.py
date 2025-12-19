from flask import Flask

from src.collector import start_collection


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    start_collection()

    @app.route("/_status/check")
    def status():
        return "OK"

    return app



v = {
    'applications': {
        'canonical-com': {
            'base': {'channel': '22.04/stable', 'name': 'ubuntu', 'unknown_fields': {}},
            'can_upgrade_to': '',
            'charm': 'ch:amd64/canonical-com-11',
            'charm_channel': 'latest/beta',
            'charm_profile': '',
            'charm_rev': 11,
            'charm_version': '',
            'endpoint_bindings': {'': 'alpha', 'grafana-dashboard': 'alpha', 'ingress': 'alpha', 'logging': 'alpha', 'metrics-endpoint': 'alpha', 'secret-storage': 'alpha'},
            'err': None,
            'exposed': False,
            'exposed_endpoints': {},
            'int_': 1,
            'life': '',
            'meter_statuses': {},
            'provider_id': 'a07abcf4-d6d1-4750-a6c6-e213e410b1ae',
            'public_address': '10.96.131.252',
            'relations': {'ingress': ['nginx-ingress-integrator'], 'secret-storage': ['canonical-com']},
            'status': {'data': {}, 'err': None, 'info': '', 'kind': '', 'life': '', 'since': '2025-12-17T16:16:13.334639017Z', 'status': 'active', 'version': '', 'unknown_fields': {}},
            'subordinate_to': [],
            'units': {
                'canonical-com/0': {
                    'address': '10.244.0.9',
                    'agent_status': {'data': {}, 'err': None, 'info': '', 'kind': '', 'life': '', 'since': '2025-12-17T16:16:13.656747744Z', 'status': 'idle', 'version': '3.6.12', 'unknown_fields': {}},
                    'charm': '',
                    'leader': True,
                    'machine': '',
                    'opened_ports': [],
                    'provider_id': 'canonical-com-0',
                    'public_address': '',
                    'subordinates': {},
                    'workload_status': {'data': {}, 'err': None, 'info': '', 'kind': '', 'life': '', 'since': '2025-12-17T16:16:13.313449494Z', 'status': 'active', 'version': '', 'unknown_fields': {}},
                    'workload_version': '',
                    'unknown_fields': {}
                }
            },
            'workload_version': '',
            'unknown_fields': {}
        },
        'nginx-ingress-integrator': {
            'base': {'channel': '22.04/stable', 'name': 'ubuntu', 'unknown_fields': {}},
            'can_upgrade_to': '',
            'charm': 'ch:amd64/nginx-ingress-integrator-203',
            'charm_channel': 'latest/stable',
            'charm_profile': '',
            'charm_rev': 203,
            'charm_version': '',
            'endpoint_bindings': {'': 'alpha', 'certificates': 'alpha', 'ingress': 'alpha', 'nginx-peers': 'alpha', 'nginx-route': 'alpha'},
            'err': None,
            'exposed': False,
            'exposed_endpoints': {},
            'int_': 1,
            'life': '',
            'meter_statuses': {},
            'provider_id': '9159160f-8a1b-47de-a1ea-f24ef2d86653',
            'public_address': '10.96.84.181',
            'relations': {'ingress': ['canonical-com'], 'nginx-peers': ['nginx-ingress-integrator']},
            'status': {'data': {}, 'err': None, 'info': '', 'kind': '', 'life': '', 'since': '2025-12-17T16:17:55.751726116Z', 'status': 'active', 'version': '', 'unknown_fields': {}},
            'subordinate_to': [],
            'units': {
                'nginx-ingress-integrator/0': {
                    'address': '10.244.0.2',
                    'agent_status': {'data': {}, 'err': None, 'info': '', 'kind': '', 'life': '', 'since': '2025-12-17T16:18:03.670367005Z', 'status': 'idle', 'version': '3.6.12', 'unknown_fields': {}},
                    'charm': '',
                    'leader': True,
                    'machine': '',
                    'opened_ports': [],
                    'provider_id': 'nginx-ingress-integrator-0',
                    'public_address': '',
                    'subordinates': {},
                    'workload_status': {'data': {}, 'err': None, 'info': '', 'kind': '', 'life': '', 'since': '2025-12-17T16:17:55.751726116Z', 'status': 'active', 'version': '', 'unknown_fields': {}},
                    'workload_version': '24.2.0',
                    'unknown_fields': {}
                }
            },
            'workload_version': '24.2.0',
            'unknown_fields': {}
        }
    },
    'branches': {},
    'controller_timestamp': '2025-12-19T09:16:33.043913086Z',
    'filesystems': [],
    'machines': {},
    'model': {
        'available_version': '',
        'cloud_tag': 'cloud-kind-kind',
        'meter_status': {'color': '', 'message': '', 'unknown_fields': {}},
        'model_status': {'data': {}, 'err': None, 'info': '', 'kind': '', 'life': '', 'since': '2025-12-08T07:22:07.829755394Z', 'status': 'available', 'version': '', 'unknown_fields': {}},
        'name': 'local-model',
        'region': None,
        'sla': 'unsupported',
        'type_': 'caas',
        'version': '3.6.12',
        'unknown_fields': {}
    },
    'offers': {},
    'relations': [
        {
            'endpoints': [
                {'application': 'canonical-com', 'name': 'secret-storage', 'role': 'peer', 'subordinate': False, 'unknown_fields': {}}
            ],
            'id_': 0,
            'interface': 'secret-storage',
            'key': 'canonical-com:secret-storage',
            'scope': 'global',
            'status': {'data': {}, 'err': None, 'info': '', 'kind': '', 'life': '', 'since': '2025-12-08T07:24:01.601345398Z', 'status': 'joined', 'version': '', 'unknown_fields': {}},
            'unknown_fields': {}
        },
        {
            'endpoints': [
                {'application': 'canonical-com', 'name': 'ingress', 'role': 'requirer', 'subordinate': False, 'unknown_fields': {}},
                {'application': 'nginx-ingress-integrator', 'name': 'ingress', 'role': 'provider', 'subordinate': False, 'unknown_fields': {}}
            ],
            'id_': 2,
            'interface': 'ingress',
            'key': 'canonical-com:ingress nginx-ingress-integrator:ingress',
            'scope': 'global',
            'status': {'data': {}, 'err': None, 'info': '', 'kind': '', 'life': '', 'since': '2025-12-08T07:25:09.156982201Z', 'status': 'joined', 'version': '', 'unknown_fields': {}},
            'unknown_fields': {}
        },
        {
            'endpoints': [
                {'application': 'nginx-ingress-integrator', 'name': 'nginx-peers', 'role': 'peer', 'subordinate': False, 'unknown_fields': {}}
            ],
            'id_': 1,
            'interface': 'nginx-instance',
            'key': 'nginx-ingress-integrator:nginx-peers',
            'scope': 'global',
            'status': {'data': {}, 'err': None, 'info': '', 'kind': '', 'life': '', 'since': '2025-12-08T07:24:12.772112015Z', 'status': 'joined', 'version': '', 'unknown_fields': {}},
            'unknown_fields': {}
        }
    ],
    'remote_applications': {},
    'storage': [],
    'volumes': [],
    'unknown_fields': {}
}