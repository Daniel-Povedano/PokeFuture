import pymongo
import requests

# Conexión a la base de datos MongoDB
client = pymongo.MongoClient("mongodb://pokefuture:27017/")

db = client["pokeapi"]

collection = db["pokemons"]
usuarios_collectio = db["usuarios"]

# Obtención de los datos de la API PokeAPI y agregándolos a la colección de MongoDB
response = requests.get('https://pokeapi.co/api/v2/pokemon?limit=1010&offset=0')
data = response.json()

pokemons_agregados = 0
pokemons_actualizados = 0

for pokemon in data['results']:
    pokemon_details = requests.get(pokemon['url']).json()
    pokemon_id = pokemon_details['id']

    # Verificar si el pokemon ya existe en la colección
    existing_pokemon = collection.find_one({'id': pokemon_id})

    if existing_pokemon is None:
        # Si el pokemon no existe, lo agregamos
        result = collection.insert_one(pokemon_details)
        if result.inserted_id:
            pokemons_agregados += 1
    else:
        # Si el pokemon ya existe, lo actualizamos
        result = collection.update_one(
                        {'id': pokemon_id},
                        {'$setOnInsert': pokemon_details},
                        upsert=True
                    )
        if result.modified_count == 1:
            pokemons_actualizados += 1

if pokemons_agregados > 0:
    print(f"{pokemons_agregados} nuevos pokemons agregados a la base de datos")
if pokemons_actualizados > 0:
    print(f"{pokemons_actualizados} pokemons actualizados en la base de datos")
if pokemons_agregados == 0 and pokemons_actualizados == 0:
    print("No se han agregado ni actualizado pokemons en la base de datos")
