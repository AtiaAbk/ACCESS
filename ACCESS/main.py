from config.settings import (
    APP_NAME,
    APP_FULL_NAME,
    VERSION,
    ENVIRONMENT,
    DEBUG,
)

from core.engine import AccessEngine


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
    print()

    engine = AccessEngine()

    print("Type 'exit' to close ACCESS.")
    print()

    while engine.running:

        user_input = input("You: ")

        if user_input.lower().strip() == "exit":
            engine.stop()
            print("ACCESS: Goodbye.")
            break

        response = engine.process(user_input)

        print(f"ACCESS: {response}")


if __name__ == "__main__":
    main()