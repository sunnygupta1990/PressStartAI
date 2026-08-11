
from src.services.resource_manager import ResourceManager


class FakeConfig:
    data = {
        "performance": {
            "enabled": True,
            "target_cpu_percent": 85,
            "target_ram_percent": 70,
            "high_ram_percent": 82,
            "cpu_reserve_cores": 1,
            "maximum_workers": 8,
        }
    }


def test_resource_manager_returns_at_least_one_worker():
    manager = ResourceManager(FakeConfig())
    assert manager.workers(
        task_name="test",
        item_count=1,
        memory_per_worker_mb=100,
    ) == 1


def test_config_has_performance_targets():
    manager = ResourceManager(FakeConfig())
    assert manager.target_cpu_percent == 85
    assert manager.target_ram_percent == 70
    assert manager.high_ram_percent == 82
