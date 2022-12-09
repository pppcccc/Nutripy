import json
import time
import sys
from datetime import date, timedelta
from textx import metamodel_from_file

nutripy_mm = metamodel_from_file('nutripy.tx')
nutripy_model = nutripy_mm.model_from_file('daily.nutripy')


# global variables to store the data
macros = []
eaten_info = {}
remaining_info = {}
user_info = {}
goal_info = {}

def weight_loss_time(weight_desired, current_weight, deficit):
    if current_weight > weight_desired:
        weight_to_lose = int(current_weight) - int(weight_desired)
        # 3500 calories in 1 lb of fat
        # 5 lbs * 3500 = 17500 / deficit (500) = 35 days
        if deficit != 0:
            days = int((weight_to_lose * 3500) / int(deficit))
        else:
            raise Exception("Must be in a caloric deficit to lose weight")
        return days
    else:
        raise Exception("Current weight must be higher than desired weight")


def fat_loss_time(desired_bf, current_bf, current_weight, deficit):
    if current_bf > desired_bf:
        # for example:
        # 18-14 = 4% to lose, 4%/100 = 0.04
        bodyfat_to_lose = (current_bf-desired_bf)/100
        # 0.04 * 205 = 8.2, now we use weight loss time calculator function
        bodyfat_in_weight = bodyfat_to_lose*current_weight
        return weight_loss_time(current_weight-bodyfat_in_weight, current_weight, deficit)

    else:
        raise Exception("Current bf must be higher than desired bf")


def initialize_db(model):
    for macro in model.macros:
        try:
            if macro.grams_weight > 0:
                macros.append({"name": macro.foodname, "weight": f'{macro.grams_weight} g', "calories": macro.calories, "protein": macro.protein, "carbs": macro.carbs, "fat": macro.fat})
            else:
                macros.append({"name": macro.foodname, "weight": f'{macro.oz_weight} oz', "calories": macro.calories, "protein": macro.protein, "carbs": macro.carbs, "fat": macro.fat})
        except:
            raise Exception("Could not add a food to the database.")


def retrieve_food(food_id, amount):
    # method to get the amount (100) and measurement (g)
    def amount_and_measurement(s):
        idx = s.find(' ')
        measurement = s[idx+1:]
        amount = float(s[:idx])

        return amount, measurement

    for food in macros:
        if food['name'] == food_id:
            # calculate the amount diff (1000g? then see how many grams arei n the food's serving and calculate)
            food_weight, food_measurement = amount_and_measurement(amount)
            db_weight, db_measurement = amount_and_measurement(food['weight'])

            if food_measurement == 'oz':
                food_weight = food_weight*28

            if db_measurement == 'oz':
                db_weight = db_weight*28

            calculated_weight = food_weight/db_weight

            calories = food['calories'] * calculated_weight
            protein = food['protein'] * calculated_weight
            carbs = food['carbs'] * calculated_weight
            fat = food['fat'] * calculated_weight
            
            return int(calories), int(protein), int(carbs), int(fat)


def calculate_split(calories):
    split = nutripy_model.userdata.split
    protein, carbs, fat = split.n_protein, split.n_carbs, split.n_fat
    protein = int(((protein/100) * calories) / 4)
    carbs = int(((carbs/100) * calories) / 4)
    fat = int(((fat/100) * calories) / 9)

    return protein, carbs, fat


def add_macros(model, file):
    for food in model.foods:
        if not food.calories:
            if food.grams_weight != 0:
                food_calories, food_protein, food_carbs, food_fat = retrieve_food(food.food_name, f'{food.grams_weight} g')
            else:
                food_calories, food_protein, food_carbs, food_fat = retrieve_food(food.food_name, f'{food.oz_weight} oz')

            eaten_info['calories'] += food_calories
            eaten_info['protein'] += food_protein
            eaten_info['carbs'] += food_carbs
            eaten_info['fat'] += food_fat

            remaining_info['calories'] -= food_calories
            remaining_info['protein'] -= food_protein
            remaining_info['carbs'] -= food_carbs
            remaining_info['fat'] -= food_fat

        else:
            eaten_info['calories'] += food.calories
            eaten_info['protein'] += food.protein
            eaten_info['carbs'] += food.carbs
            eaten_info['fat'] += food.fat

            remaining_info['calories'] -= food.calories
            remaining_info['protein'] -= food.protein
            remaining_info['carbs'] -= food.carbs
            remaining_info['fat'] -= food.fat

    write_json(file)


def undo_macros(model, file):
    for food in model.foods:
        if not food.calories:
            if food.grams_weight != 0:
                food_calories, food_protein, food_carbs, food_fat = retrieve_food(food.food_name, f'{food.grams_weight} g')
            else:
                food_calories, food_protein, food_carbs, food_fat = retrieve_food(food.food_name, f'{food.oz_weight} oz')

            eaten_info['calories'] -= food_calories
            eaten_info['protein'] -= food_protein
            eaten_info['carbs'] -= food_carbs
            eaten_info['fat'] -= food_fat

            remaining_info['calories'] += food_calories
            remaining_info['protein'] += food_protein
            remaining_info['carbs'] += food_carbs
            remaining_info['fat'] += food_fat

        else:
            eaten_info['calories'] -= food.calories
            eaten_info['protein'] -= food.protein
            eaten_info['carbs'] -= food.carbs
            eaten_info['fat'] -= food.fat

            remaining_info['calories'] += food.calories
            remaining_info['protein'] += food.protein
            remaining_info['carbs'] += food.carbs
            remaining_info['fat'] += food.fat

    write_json(file)


def parse_model(model):
    user_info['gender'] = model.userdata.user_gender
    user_info['age'] = model.userdata.age
    user_info['weight']  = model.userdata.weight
    user_info['height']  = model.userdata.height
    user_info['goal']  = model.userdata.user_goal
    user_info['activity'] = model.userdata.activity
    goal_info['calories'] = calculate_calories(user_info['weight'], user_info['height'], user_info['age'], user_info['gender'], user_info['goal'], user_info['activity'])

    remaining_info['calories'] = goal_info['calories'] if remaining_info['calories'] == 0  else remaining_info['calories']

    goal_info['protein'], goal_info['carbs'], goal_info['fat'] = calculate_split(goal_info['calories'])

    remaining_info['protein'] = goal_info['protein'] if remaining_info['protein'] == 0  else remaining_info['protein']
    remaining_info['carbs'] = goal_info['carbs'] if remaining_info['carbs'] == 0  else remaining_info['carbs']
    remaining_info['fat'] = goal_info['fat'] if remaining_info['fat'] == 0  else remaining_info['fat']


def calculate_calories(weight, height, age, gender, goal, activity_level):
    # https://www.verywellfit.com/how-many-calories-do-i-need-each-day-2506873
    # calculate AMR for accurate maintenance numbers

    if weight > 0:
        if gender == 'male':
            BMR = 66.47 + (6.24 * weight) + (12.7 * height) - (6.75 * age)
        else:
            BMR = 65.51 + (4.35 * weight) + (4.7 * height) - (4.7 * age)

        if activity_level == 0:
            AMR = BMR * 1.2

        elif 1 <= activity_level <= 2:
            AMR = BMR * 1.375

        elif 3 <= activity_level <= 5:
            AMR = BMR * 1.55

        elif 6 <= activity_level <= 7:
            AMR = BMR * 1.8

        else:
            raise Exception("Activity level must be between 0 and 7")
        

        if goal == "deficit":
            # 1 lb of fat lost a week
            # 500 is a safe number to cut on
            return int(AMR - 500)

        elif goal == "maintenance":
            return int(AMR)

        elif goal == "surplus":
            # most calories past 200 surplus just become fat
            # so we will do a small surplus
            # (16 calories surplus daily builds 10 lbs of muscle a year)
            return int(AMR + 200)

    else:
        raise Exception("Weight must be a positive integer")


def read_json(file):
    global eaten_info
    global remaining_info
    global user_info
    global goal_info
    try:
        with open(file, "r") as read_file:
            content = json.load(read_file)
        
        eaten_info = content['eaten']
        remaining_info = content['remaining']
        user_info = content['user']
        goal_info = content['goal']


    except Exception:
        data = {
            "user":{
                "height": 0,
                "weight": 0,
                "goal": "maintenance",
                "activity": 0
            },
            "goal": {
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fat": 0
            },
            "eaten": {
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fat": 0
            },
            "remaining":{
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fat": 0
            }
        }

        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        eaten_info = data['eaten']
        remaining_info = data['remaining']
        user_info = data['user']
        goal_info = data['goal']


def write_json(file):
    global eaten_info
    global remaining_info
    global user_info
    global goal_info
    try:
        data = {
            "user": user_info,
            "goal": goal_info,
            "eaten": eaten_info,
            "remaining": remaining_info
        }
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    except Exception as err:
        print(f'ran into an error loading json \n{err}')


def print_stats():
    print(f"Data for a {user_info['weight']} pound {user_info['gender']} who is {user_info['height']} inches tall.\n")
    print(f"Daily Macronutrient Goals:\n{goal_info['calories']} calories\n{goal_info['protein']}g protein\n{goal_info['carbs']}g carbs\n{goal_info['fat']}g fat\n")
    print(f"Consumed Today:\n{eaten_info['calories']} calories\n{eaten_info['protein']}g protein\n{eaten_info['carbs']}g carbs\n{eaten_info['fat']}g fat\n")
    print(f"Remaining Today:\n{remaining_info['calories']} calories\n{remaining_info['protein']}g protein\n{remaining_info['carbs']}g carbs\n{remaining_info['fat']}g fat\n")


if __name__ == "__main__":
    operation = sys.argv[1] if len(sys.argv) > 1 else None
    initialize_db(nutripy_model)


    if len(sys.argv) > 2:
        if sys.argv[2] == 'yesterday':
            yesterday = date.today() - timedelta(days=1)
            filename = f'{yesterday}.json'

        else:
            filename = sys.argv[2]

    else: 
        filename = f'{date.today()}.json'
        

    if operation == 'add':
        read_json(filename)
        parse_model(nutripy_model)
        add_macros(nutripy_model, filename)
        print_stats()


    elif operation == 'display':
        read_json(filename)
        parse_model(nutripy_model)
        print_stats()


    elif operation == 'undo':
        read_json(filename)
        parse_model(nutripy_model)
        undo_macros(nutripy_model, filename)
        print_stats()


    elif operation == 'calculate':
        calc_args = [sys.argv[2]] + [int(arg) for arg in sys.argv[3:]]

        if calc_args[0] == 'weightloss':
            days = weight_loss_time(calc_args[1], calc_args[2], calc_args[3])
            print(f'To lose {calc_args[2]-calc_args[1]} lbs to get to {calc_args[1]} lbs at a {calc_args[3]} calorie deficit it will take {days} days.')

        elif calc_args[0] == 'fatloss':
            days = fat_loss_time(calc_args[1], calc_args[2], calc_args[3], calc_args[4])
            print(f'To lose {calc_args[2]-calc_args[1]}% bodyfat to get to {calc_args[1]}% at a {calc_args[4]} calorie deficit it will take {days} days.')

    else:
        print('Please enter an argument:')
        print('Format 1: python nutripy.py add {json file/no file = today}')
        print('Format 2: python nutripy.py display {json file/no file = today}')
        print('Format 3: python nutripy.py calculate weightloss {desired weight} {current weight} {caloric deficit}')
        print('Format 4: python nutripy.py calculate fatloss {desired body fat} {current body fat} {current weight} {caloric deficit}')
    