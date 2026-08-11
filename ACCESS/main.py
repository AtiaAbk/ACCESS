from config.settings import (
    APP_NAME,
    APP_FULL_NAME,
    VERSION,
    ENVIRONMENT,
    DEBUG,
)


def main():
    print("=" * 60)
    print(APP_NAME)
    print(APP_FULL_NAME)
    print(f"Version: {VERSION}")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Debug: {DEBUG}")
    print("=" * 60)

    print("ACCESS is starting...")
    print("System initialization complete.")


if __name__ == "__main__":
    main()