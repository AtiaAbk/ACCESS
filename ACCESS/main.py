from config.settings import APP_NAME, APP_FULL_NAME, VERSION


def main():
    print("=" * 60)
    print(f"{APP_NAME}")
    print(f"{APP_FULL_NAME}")
    print(f"Version: {VERSION}")
    print("=" * 60)
    print("ACCESS is starting...")
    print("System initialization complete.")


if __name__ == "__main__":
    main()