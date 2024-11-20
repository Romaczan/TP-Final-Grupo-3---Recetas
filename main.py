import telebot
import requests
from telebot import types
import os
from dotenv import load_dotenv

load_dotenv()

# POR FAVOR PONGNA SUS TOKENS, MODIFIQUE EN .env
tk = os.getenv("tk_telegram")
bot = telebot.TeleBot(tk)
SPOONACULAR_API_KEY = os.getenv("spoonacular_api")
SPOONACULAR_URL = "https://api.spoonacular.com/recipes/complexSearch"

# Es donde se va a almacenar los datos del usuario
datos_de_usuario = {}

######################################################################################################################

""" Botón de Bienvenida e Inicio """

@bot.message_handler(commands=['start'])
def mensaje_de_bienvenida(message):
    nombre_usuario = message.from_user.first_name
    texto_bienvenida = (
        f"Bienvenido, {nombre_usuario}!\n"
        "Este bot te ayudara a encontrar recetas basadas en los ingredientes y preferencias alimenticias.\n"
        "Por favor, selecciona una de las opciones:"
    )

    # Crear el teclado p
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    boton_ingresar_ingredientes = types.KeyboardButton("Ingresar Ingredientes")
    boton_ingresar_preferencias = types.KeyboardButton("Ingresar Preferencias")
    boton_buscar_recetas = types.KeyboardButton("Buscar Recetas")
    markup.add(boton_ingresar_ingredientes)
    markup.add(boton_ingresar_preferencias)
    markup.add(boton_buscar_recetas)

    # Enviar el mensaje de bienvenida asi queda todo lindo
    bot.send_message(message.chat.id, texto_bienvenida, reply_markup=markup)

######################################################################################################################

""" Manejar el botón para ingresar ingredientes """

@bot.message_handler(func=lambda message: message.text == "Ingresar Ingredientes")
def ingresar_ingredientes(message):
    msg = bot.send_message(message.chat.id, "Por favor, ingresa los ingredientes separados por comas.")
    bot.register_next_step_handler(msg, procesar_ingredientes)

def procesar_ingredientes(message):
    usuario_id = message.from_user.id
    ingredientes = message.text.strip()

    if not ingredientes:
        msg = bot.send_message(message.chat.id, "No se encuentra ingresado ningun ingrediente. Por favor ingresa un ingrediente.")
        bot.register_next_step_handler(msg, procesar_ingredientes)
        return

    # Guardar los ingredientes en datos_de_usuario
    if usuario_id not in datos_de_usuario:
        datos_de_usuario[usuario_id] = {}
    datos_de_usuario[usuario_id]['ingredientes'] = ingredientes

    bot.send_message(message.chat.id, f"Los ingredientes '{ingredientes}' han sido guardados.")

    # Mostrar opciones despues de ingresar ingredientes
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    boton_ingresar_preferencias = types.KeyboardButton("Ingresar Preferencias")
    boton_buscar_recetas = types.KeyboardButton("Buscar Recetas")
    markup.row(boton_ingresar_preferencias)
    markup.row(boton_buscar_recetas)

    bot.send_message(message.chat.id, "Por favor, ingresa preferencias o busca recetas", reply_markup=markup)

######################################################################################################################

""" Manejar el botón para ingresar preferencias """

@bot.message_handler(func=lambda message: message.text == "Ingresar Preferencias")
def ingresar_preferencias(message):
    msg = bot.send_message(message.chat.id, "Por favor ingresa tus preferencias alimentarias (vegan, gluten free, etc), en caso de no necesitar una siga con Buscar Receta.")
    bot.register_next_step_handler(msg, procesar_preferencias)

def procesar_preferencias(message):
    usuario_id = message.from_user.id
    preferencias = message.text.strip()

    if not preferencias:
        msg = bot.send_message(message.chat.id, "No ingresaste ninguna preferencia. Por favor prueba de nuevo.")
        bot.register_next_step_handler(msg, procesar_preferencias)
        return

    if usuario_id not in datos_de_usuario:
        datos_de_usuario[usuario_id] = {}
    datos_de_usuario[usuario_id]['preferencias'] = preferencias

    bot.send_message(message.chat.id, f"Las preferencias '{preferencias}' han sido guardadas.")

    # Mostrar opciones despues de ingresar preferencias
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    boton_ingresar_ingredientes = types.KeyboardButton("Ingresar Ingredientes")
    boton_buscar_recetas = types.KeyboardButton("Buscar Recetas")
    markup.row(boton_ingresar_ingredientes)
    markup.row(boton_buscar_recetas)

    bot.send_message(message.chat.id, "Que sigue?", reply_markup=markup)

def validate_user_input(ingredients, preferences):
    return bool(ingredients and preferences)

######################################################################################################################

""" Preparar los datos para la que la API busque recetas """

def prepare_data_for_api(ingredients, preferences):
    formatted_ingredients = ingredients.replace(" ", "")
    formatted_preferences = preferences.lower()
    return {
        "ingredients": formatted_ingredients,
        "preferences": formatted_preferences
    }

def fetch_recipes_from_spoonacular(ingredients, preferences):
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "includeIngredients": ingredients,
        "diet": preferences,
        "apiKey": SPOONACULAR_API_KEY,
        "number": 5 
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        print(f"API Response Status: {response.status_code}")
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud a la API: {e}")
        return None

#####################################################################################################

""" Manejar el botón de buscar recetas """

@bot.message_handler(func=lambda message: message.text == "Buscar Recetas")
def search_recipes(message):
    usuario_id = message.from_user.id

    if usuario_id in datos_de_usuario:
        ingredients = datos_de_usuario[usuario_id].get('ingredientes', '')
        preferences = datos_de_usuario[usuario_id].get('preferencias', '')

        if validate_user_input(ingredients, preferences):
            data = prepare_data_for_api(ingredients, preferences)
            recipes = fetch_recipes_from_spoonacular(data["ingredients"], data["preferences"])

            if recipes and "results" in recipes:
                if recipes["results"]:
                    for recipe in recipes["results"]:
                        recipe_info = f"Recipe: {recipe['title']}\n"
                        recipe_info += f"URL: https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-').lower()}-{recipe['id']}\n"
                        bot.send_message(message.chat.id, recipe_info)
                else:
                    bot.send_message(message.chat.id, "No se han encontrado recetas que concuerden con busqueda.")
            else:
                bot.send_message(message.chat.id, "Hubo un problema al obtener las recetas. Por favor chequea que la API Key sea correcta.")
        else:
            bot.send_message(message.chat.id, "Por favor asegurate que hayas ingresado tus ingredientes y preferencias.")
    else:
        bot.send_message(message.chat.id, "Por favor ingresa tus ingredientes y preferencias primero.")

if __name__ == "__main__":
    print("Bot iniciado correctamente...")
    bot.polling(none_stop=True)
