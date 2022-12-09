# Nutripy
Nutripy is a DSL written in Python and TextX that allows for macronutrient and calorie tracking. It uses the CLI and stores everything in a daily JSON file.
Nutripy supports adding calories and macronutrients specified in a .nutripy file along with a database of foods with defined macronutrients.
Dependencies needed: textx, datetime

There are currently 4 ways to use nutripy:
Format 1: python nutripy.py add {json file/no file = today}
Format 2: python nutripy.py display {json file/no file = today}
Format 3: python nutripy.py calculate weightloss {desired weight} {current weight} {caloric deficit}
Format 4: python nutripy.py calculate fatloss {desired body fat} {current body fat} {current weight} {caloric deficit}
