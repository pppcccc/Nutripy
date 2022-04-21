import json
import time
from textx import metamodel_from_file

nutripy_mm = metamodel_from_file('nutripy.tx')
nutripy_model = nutripy_mm.model_from_file('daily.nutripy')

# global variables to store the data
eaten_info = {}
remaining_info = {}
user_info = {}
goal_info = {}


def parse_model(model, file):
    user_info['weight']  = model.userdata.weight
    user_info['height']  = model.userdata.height
    user_info['goal']  = model.userdata.user_goal
    user_info['gymgoer']  = model.userdata.gymgoer
    goal_info['calories'] = calculate_calories(user_info['weight'], user_info['goal'])
    remaining_info['calories'] = goal_info['calories'] if remaining_info['calories'] == 0  else remaining_info['calories']

    if user_info['gymgoer'] == 'yes':
        goal_info['protein'] = 1 * user_info['weight']
        goal_info['carbs'] = 1.2 * user_info['weight']
        # carbs & protein are 4 cal per gram
        result = goal_info['calories'] - (goal_info['protein'] + goal_info['carbs'])*4
        # fat is 9 calories per gram, round to 2 decimal places
        result = int(round(result/9, 2))
        goal_info['fat'] = result

        remaining_info['protein'] = goal_info['protein'] if remaining_info['protein'] == 0  else remaining_info['protein']
        remaining_info['carbs'] = goal_info['carbs'] if remaining_info['carbs'] == 0  else remaining_info['carbs']
        remaining_info['fat'] = goal_info['fat'] if remaining_info['fat'] == 0  else remaining_info['fat']

    else:
        goal_info['protein'] = 0.5 * user_info['weight']
        goal_info['carbs'] = 1.7 * user_info['weight']
        # carbs & protein are 4 cal per gram
        result = goal_info['calories'] - (goal_info['protein'] + goal_info['carbs'])*4
        # fat is 9 calories per gram, round to 2 decimal places
        result = int(round(result/9, 2))
        goal_info['fat'] = result

        remaining_info['protein'] = goal_info['protein'] if remaining_info['protein'] == 0  else remaining_info['protein']
        remaining_info['carbs'] = goal_info['carbs'] if remaining_info['carbs'] == 0  else remaining_info['carbs']
        remaining_info['fat'] = goal_info['fat'] if remaining_info['fat'] == 0  else remaining_info['fat']

    for food in model.foods:
        eaten_info['calories'] += food.calories
        eaten_info['protein'] += food.protein
        eaten_info['carbs'] += food.carbs
        eaten_info['fat'] += food.fat

        remaining_info['calories'] -= food.calories
        remaining_info['protein'] -= food.protein
        remaining_info['carbs'] -= food.carbs
        remaining_info['fat'] -= food.fat


    write_json(file)
    

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
                "gymgoer": "no"
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

        with open('eaten.json', 'w', encoding='utf-8') as f:
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
        with open('eaten.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    except Exception as err:
        print(f'ran into an error loading json \n{err}')


def calculate_calories(weight, goal):
    if goal == 'deficit':
        if 0 < weight:
            formula = weight * 12
            return formula
        else:
            raise Exception("weight can not be lower than 0")

    elif goal == 'surplus':
        if 0 < weight:
            formula = weight * 18
            return formula 
        else:
            raise Exception("weight can not be lower than 0")
    else:
        if 0 < weight:
            formula = weight * 15
            return formula
        else:
            raise Exception("weight can not be lower than 0")


if __name__ == "__main__":
    filename = 'eaten.json'
    read_json(filename)
    parse_model(nutripy_model, filename)