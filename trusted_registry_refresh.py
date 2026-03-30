from config import AppConfig
from trusted_registry import write_trusted_registry_files


def main() -> None:
    config = AppConfig()
    role_ids = sorted(path.stem for path in config.roles_dir.glob('*.ptn') if path.stem.lower() != 'core_terms')
    manifest, cache = write_trusted_registry_files(
        roles_dir=config.roles_dir,
        manifest_path=config.trusted_registry_manifest_path,
        cache_path=config.trusted_registry_cache_path,
        role_ids=role_ids,
        signing_key=config.trusted_registry_signing_key or '',
        key_id=config.trusted_registry_key_id,
        signed_by=config.trusted_registry_signed_by,
    )
    print(config.trusted_registry_manifest_path)
    print(config.trusted_registry_cache_path)
    print(sorted(manifest['roles'].keys()))
    print(manifest['signature']['key_id'])
    print(len(cache['entries']))


if __name__ == '__main__':
    main()
