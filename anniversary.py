import time

score = 0

print("=" * 50)
print("❤️ WELCOME MOM & DAD ❤️")
print("A Special Anniversary Surprise")
print("=" * 50)

input("\nPress Enter to start the journey...")

# Question 1
print("\n🌟 Question 1")
ans = input("Who is the best cook in the house? ")

if ans.lower() == "mom":
    print("🎉 Correct! Mom's food is amazing!")
    score += 1
else:
    print("😄 Nice try! We all know the answer!")

# Question 2
print("\n🌟 Question 2")
ans = input("Who tells the funniest jokes? ")

if ans.lower() == "dad":
    print("😂 Absolutely!")
    score += 1
else:
    print("😁 Good guess!")

# Question 3
print("\n🌟 Question 3")
ans = input("Who loves the family the most? ")

print("❤️ Correct! Both Mom and Dad do!")

print("\n🔓 Secret Message Unlocked...")
time.sleep(2)

print("\n" + "=" * 50)
print("Dear Mom & Dad,")
print()
print("Thank you for every sacrifice.")
print("Thank you for every smile.")
print("Thank you for every lesson.")
print("Thank you for making our family beautiful.")
print()
print("I am lucky to be your son.")
print("=" * 50)

print("\n🎂 Celebration starts in...")

for i in range(5, 0, -1):
    print(i)
    time.sleep(1)

print("\n✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨")
print("🎉 HAPPY ANNIVERSARY 🎉")
print("✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨")

time.sleep(1)

heart = """
  *****     *****
 ********   ********
********************
 ******************
  ****************
    ************
      ********
        ****
          *
"""

print(heart)

print("❤️ MOM & DAD ❤️")
print()
print("Happy Anniversary!")
print()
print("May your love continue to grow")
print("stronger every year.")
print()
print("With Love,")
print("Kirtan ❤️")

print(f"\n⭐ Fun Score: {score}/2")
input("\nPress Enter to exit...")