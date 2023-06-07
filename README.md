# PokeFuture

- Flask APP + MongoDB en Docker


## Descripción del proyecto
- Este proyecto es una aplicacion Flask que se inicia mediante un docker-compose junto a una base de datos MongoDB y un Python que actualiza la base de datos mediante cogiendo datos a una API externa.

## Capturas de pantalla 
<img src="https://github.com/Daniel-Sid/PokeFuture/assets/104014451/84083bca-dad2-4e2c-b981-8b8cd1712ddd" alt="Texto alternativo" width="600" height="300">
<img src="https://github.com/Daniel-Sid/PokeFuture/assets/104014451/e35e230c-ad9d-4e27-9185-93c9356fffe0" alt="Texto alternativo" width="600" height="300">
<img src="https://github.com/Daniel-Sid/PokeFuture/assets/104014451/b957d897-f783-4912-8c6a-2213247856de" alt="Texto alternativo" width="600" height="300">

## Instalación
- Para poder instalarlo necesitaras

1. Instalar Python mediante su Pagina oficial y seguir los pasos
2. Recomendado Visual Studio Code
3. Instalar Flask con **pip install flask**
4. Instalar DockerDesktop
5. Descargar el proyecto y abrirlo en un entorno de desarrollo
6. Poner en la terminal docker-compose up estando en el mismo directorio que el docker-compose.yml

- En caso de que no funcione cualquiera de los pasos hay un manual en /Manuales > Manual del programador

## Uso
- Una vez que los contenedores estén en funcionamiento, puedes acceder a la aplicación Flask en tu navegador web en http://localhost. La aplicación te mostrará información actualizada de los datos obtenidos de la API externa y almacenados en MongoDB.  

## Créditos
-  **Flask** - Framework web utilizado en este proyecto.
-  **MongoDB** - Base de datos NoSQL utilizada para almacenar los datos.
-  **API PokeApi** - Fuente de datos utilizada para realizar actualizaciones en MongoDB.
