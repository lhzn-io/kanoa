import matplotlib.pyplot as plt
import numpy as np

from kanoa import AnalyticsInterpreter

# 1. Simulate a projectile (with a bug!)
t = np.linspace(0, 10, 100)
v0 = 50
g = 9.8
# BUG: Missing t**2 in the gravity term (should be 0.5 * g * t**2)
y = v0 * t - 0.5 * g * t

plt.figure(figsize=(10, 6))
plt.plot(t, y)
plt.title("Projectile Trajectory")
plt.xlabel("Time (s)")
plt.ylabel("Height (m)")

# 2. Ask kanoa to debug
interpreter = AnalyticsInterpreter(backend="gemini")
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Simulating a projectile launch. Something looks wrong.",
    focus="Identify the physics error in the trajectory.",
)
print("kanoa's analysis:")
print(result.text)
