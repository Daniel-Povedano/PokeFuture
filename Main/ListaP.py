import os
import pathlib
from flask_caching import Cache
from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, session, url_for
from pip._vendor import cachecontrol
import google.auth.transport.requests
from pymongo import MongoClient
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import pymongo
import requests
import secrets


# Creamos una instancia de Flask y la guardamos en la variable 'app'
app = Flask(__name__)

# Creamos una instancia de Cache y la configuramos con el tipo de caché 'simple'
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Establecemos una clave secreta random para la aplicación Flask
app.secret_key = secrets.token_hex(32)

# Establecemos una variable de entorno para permitir el transporte inseguro de OAuthLib
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Creamos una instancia del cliente de MongoDB y nos conectamos a la base de datos
client = MongoClient("mongodb://pokefuture:27017/")

# Seleccionamos una base de datos llamada 'pokeapi'
db = client["pokeapi"]
db2 = client["pokeapi"]

# Creamos una colección llamada 'pokemons' y 'usuarios'
collection = db["pokemons"]
collection2 = db2["usuarios"]

# Establecemos una ID de cliente de Google y especificamos la ubicación del archivo JSON que contiene las credenciales del cliente

# IMPORTANTE ---------------------------------------------------------------------------
# IMPORTANTE ---------------------------------------------------------------------------
GoogleId = ""
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
# IMPORTANTE ---------------------------------------------------------------------------
# IMPORTANTE ---------------------------------------------------------------------------

# Creamos una instancia de la clase Flow y le pasamos las credenciales del cliente, los ámbitos de autorización y la URI de redireccionamiento
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email",
            "openid"],
    redirect_uri="http://localhost/callback"
)


# Definimos un decorador para verificar si el usuario ha iniciado sesión con Google
def login_requerido(function):
    def wrapper(*args, **kwargs):
        # Si la variable de sesión 'google_id' no existe, abortamos la solicitud con un código de error 401 (no autorizado)
        if "google_id" not in session:
            abort(401)
        # Si el usuario ha iniciado sesión, ejecutamos la función decorada
        else:
            return function()

    return wrapper


def email_en_uso(email):
    return collection2.find_one({"email": email}) is not None


def email_guardado(email):
    collection2.insert_one({"email": email})


# Definimos una ruta para la página principal de la aplicación
@app.route('/')
def principal():
    # Devolvemos una plantilla HTML usando la función 'render_template'
    return render_template('main.html')

@app.route('/main2')
def principal2():
    return render_template('main2.html')

@app.route('/redirect', methods=['POST'])
def language_redirect():
    language = request.form['language']
    if language == 'es':
        return redirect(url_for('principal2'))
    elif language == 'en':
        return redirect(url_for('principal'))
    else:
        return redirect(url_for('principal'))


# Definimos una ruta para la página de inicio de sesión de Google
@app.route('/login')
def login():
    # Obtenemos la URL de autorización de Google y un estado generado aleatoriamente
    authorization_url, state = flow.authorization_url()
    # Guardamos el estado en una variable de sesión para verificarlo más tarde
    session["state"] = state
    # Redireccionamos al usuario a la URL de autorización de Google
    return redirect(authorization_url)


# Definimos una ruta para la página protegida de la aplicación
@app.route('/protected')
# Aplicamos el decorador 'login_requerido' a la función de vista para protegerla
@login_requerido
def protected():
    # Devolvemos una cadena de texto como respuesta
    return "Protegido <a href ='/logout'><button>Logout</button></a>"


# Definimos una ruta para manejar la respuesta de Google después de que el usuario ha iniciado sesión
@app.route('/callback')
def callback():
    # Intercambiamos el código de autorización por un token de acceso y un token de actualización
    flow.fetch_token(authorization_response=request.url)

    # Verificamos que el estado generado aleatoriamente sea el mismo que el que envió Google
    if not session["state"] == request.args["state"]:
        abort(500)

    # Obtenemos los detalles del usuario a partir del token de ID de Google
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GoogleId
    )

    # Guardamos los detalles del usuario en variables de sesión
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    session["picture"] = id_info.get("picture")

    email = id_info.get("email")
    if not email_en_uso(email):
        email_guardado(email)
        return redirect("/")
    else:
        return redirect("/")

@app.route('/favorites')
def favorites():
    # Obtenemos el usuario de la base de datos basado en el email de la sesión
    usuario = db.usuarios.find_one({"email": session.get('email')})
    
    # Si el usuario no ha iniciado sesión con Google, redirigimos a la página de inicio de sesión
    if 'google_id' not in session:
        return redirect(url_for('login'))
    
    # Obtenemos la lista de favoritos del usuario
    favoritos = usuario.get('favoritos', [])
    
    if favoritos:
        return render_template('favorites.html', favoritos=favoritos)
    else:
        flash("No tienes Pokémon favoritos.", "warning")
        return render_template('favorites.html')


@app.route('/teams')
def teams():
    # Obtenemos el usuario de la base de datos basado en el email de la sesión
    usuario = db.usuarios.find_one({"email": session.get('email')})
    
    # Si el usuario no ha iniciado sesión con Google, redirigimos a la página de inicio de sesión
    if 'google_id' not in session:
        return redirect(url_for('login'))
    
    # Obtenemos el equipo del usuario
    equipo = usuario.get('teams', [])
    
    if equipo:
        return render_template('teams.html', equipo=equipo)
    else:
        flash("No tienes Pokémon en el equipo.", "warning")
        return render_template('teams.html')


@app.route('/favorito', methods=['POST'])
def favoritoUsu():
    # Si el usuario no ha iniciado sesión con Google, redirigimos a la página de inicio de sesión
    if 'google_id' not in session:
        return redirect(url_for('login'))

    # Obtenemos los detalles del Pokémon que se va a marcar como favorito
    pokemon_name = request.form['pokemon_name']
    pokemon = db.pokemons.find_one({'name': pokemon_name})

    if pokemon:
        # Obtenemos el usuario de la base de datos basado en el email de la sesión
        usuario = db.usuarios.find_one({'email': session['email']})
        favoritos = usuario.get('favoritos', [])
        favoritos.append({
            'name': pokemon['name'],
            'image': pokemon['sprites']['front_default'],
            'id': pokemon['id']
        })
        db.usuarios.update_one({'email': session['email']}, {'$set': {'favoritos': favoritos}})
    
    return redirect(url_for('listar_pokemons'))

@app.route('/teams', methods=['POST'])
def teamsUsu():
    # Si el usuario no ha iniciado sesión con Google, redirigimos a la página de inicio de sesión
    if 'google_id' not in session:
        return redirect(url_for('login'))

    # Obtenemos los detalles del Pokémon que se va a agregar al equipo
    pokemon_name = request.form['pokemon_name']
    pokemon_image = request.form['pokemon_image']
    pokemon_id = request.form['pokemon_id']
    pokemon_height = request.form['pokemon_height']
    pokemon_weight = request.form['pokemon_weight']
    pokemon_stats = request.form.getlist('pokemon_stats[]')
    pokemon_types = request.form.getlist('pokemon_types[]')

    # Obtenemos el usuario de la base de datos basado en el email de la sesión
    usuario = db.usuarios.find_one({'email': session['email']})
    teams = usuario.get('teams', [])
    teams.append({
        'name': pokemon_name,
        'image': pokemon_image,
        'id': pokemon_id,
        'height': pokemon_height,
        'weight': pokemon_weight,
        'stats': pokemon_stats,
        'types': pokemon_types
    })
    db.usuarios.update_one({'email': session['email']}, {'$set': {'teams': teams}})
    
    return redirect(url_for('listar_pokemons'))


@app.route('/remover', methods=['POST'])
def removerFavorito():
    # Si el usuario no ha iniciado sesión con Google, redirigimos a la página de inicio de sesión
    if 'google_id' not in session:
        return redirect(url_for('login'))

    pokemon_name = request.form['pokemon_name']
    usuario = db.usuarios.find_one({'email': session['email']})
    favoritos = usuario.get('favoritos', [])

    # Buscamos el índice del Pokémon en la lista de favoritos
    index = next((i for i, fav in enumerate(favoritos) if fav['name'] == pokemon_name), None)

    if index is not None:
        # Removemos el Pokémon de la lista de favoritos
        favoritos.pop(index)
        db.usuarios.update_one({'email': session['email']}, {'$set': {'favoritos': favoritos}})
    
    return redirect(url_for('listar_pokemons'))

@app.route('/removeFromTeam', methods=['POST'])
def removeFromTeam():
    # Si el usuario no ha iniciado sesión con Google, redirigimos a la página de inicio de sesión
    if 'google_id' not in session:
        return redirect(url_for('login'))

    pokemon_id = request.form['pokemon_id']

    usuario = db.usuarios.find_one({'email': session['email']})
    teams = usuario.get('teams', [])

    # Removemos el Pokémon con el ID especificado del equipo
    teams = [pokemon for pokemon in teams if pokemon['id'] != pokemon_id]

    db.usuarios.update_one({'email': session['email']}, {'$set': {'teams': teams}})

    return redirect(url_for('listar_pokemons'))

@app.route('/removeFromTeamPage', methods=['POST'])
def removeFromTeamPage():
    # Si el usuario no ha iniciado sesión con Google, redirigimos a la página de inicio de sesión
    if 'google_id' not in session:
        return redirect(url_for('login'))

    pokemon_id = request.form['pokemon_id']

    usuario = db.usuarios.find_one({'email': session['email']})
    teams = usuario.get('teams', [])

    # Removemos el Pokémon con el ID especificado del equipo
    teams = [pokemon for pokemon in teams if pokemon['id'] != pokemon_id]

    db.usuarios.update_one({'email': session['email']}, {'$set': {'teams': teams}})

    return redirect(url_for('teams'))


@app.route('/removerFavoritoInFavorites', methods=['POST'])
def removerFavoritoInFavorites():
    # Si el usuario no ha iniciado sesión con Google, redirigimos a la página de inicio de sesión
    if 'google_id' not in session:
        return redirect(url_for('login'))

    pokemon_name = request.form['pokemon_name']
    usuario = db.usuarios.find_one({'email': session['email']})
    favoritos = usuario.get('favoritos', [])

    # Buscamos el índice del Pokémon en la lista de favoritos
    index = next((i for i, fav in enumerate(favoritos) if fav['name'] == pokemon_name), None)

    if index is not None:
        # Removemos el Pokémon de la lista de favoritos
        favoritos.pop(index)
        db.usuarios.update_one({'email': session['email']}, {'$set': {'favoritos': favoritos}})
    
    return redirect(url_for('favorites'))

# Definir la ruta '/logout'
@app.route('/logout')
def logout():
    # Limpiar la sesión actual
    session.clear()
    # Redirigir al usuario a la página principal
    return redirect("/")


@app.route('/pokemons')
def listar_pokemons():
    pokemons = collection.find()
    usuario = db.usuarios.find_one({"email": session.get('email')})
    
    if 'google_id' not in session:
        return redirect(url_for('login'))
    
    equipo = usuario.get('teams', [])
    favoritos = usuario.get('favoritos', [])
    
    return render_template('lista_pokemons.html', pokemons=pokemons, favoritos=favoritos, equipo=equipo)

# Si el archivo se está ejecutando directamente (y no fue importado por otro módulo), iniciar la aplicación Flask en modo debug
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
