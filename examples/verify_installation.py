import matplotlib.pyplot as plt
import numpy as np

from kanoa import AnalyticsInterpreter


def verify_installation():
    print("🧪 Verifying kanoa installation...")

    # 1. Create a simple plot
    print("   Creating test visualization...")
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    plt.figure(figsize=(8, 4))
    plt.plot(x, y)
    plt.title("Test Sine Wave")
    plt.grid(True)

    # 2. Initialize Interpreter
    # This will use Vertex AI via ADC if GOOGLE_API_KEY is not set
    print("   Initializing Gemini backend...")
    try:
        interpreter = AnalyticsInterpreter(
            backend="gemini-3",
            # Optional: specify project/location if needed, otherwise uses defaults
            # project='your-project-id',
            # location='us-central1'
        )
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return

    # 3. Interpret
    print("   Sending request to Gemini (this may take a few seconds)...")
    try:
        result = interpreter.interpret(
            fig=plt.gcf(),
            context="Verification test run",
            focus="Confirm this is a sine wave",
        )

        if "Error" in result.text:
            print(f"❌ Interpretation failed: {result.text}")
        else:
            print("\n✅ Success! Received interpretation:")
            print("-" * 50)
            print(result.text[:500] + "..." if len(result.text) > 500 else result.text)
            print("-" * 50)
            print(f"Backend: {result.backend}")
            if result.usage:
                print(f"Cost: ${result.usage.cost:.4f}")

    except Exception as e:
        print(f"❌ Execution failed: {e}")


if __name__ == "__main__":
    verify_installation()
