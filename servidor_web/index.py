from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, make_response, Response, session,jsonify
from flask_login import LoginManager, login_required, UserMixin, login_user, logout_user
from werkzeug.datastructures import ImmutableMultiDict
from functools import wraps
import datetime
import jwt
import re
from werkzeug.datastructures import ImmutableMultiDict
#from flask_session import Session

import pyrebase

from firebase_admin import db
import firebase_admin
from firebase_admin import credentials
from collections import OrderedDict
import os
app = Flask(__name__)
# Configura la extensión Flask-Session
#Session(app)
# Configurar las credenciales de Firebase
# Inicializa la aplicación de Firebase con tus credenciales
firebase_sdk = credentials.Certificate("simulador-de-pacientes-db11b-firebase-adminsdk-447re-450c6a73e9.json")
firebase_admin.initialize_app(firebase_sdk,{'databaseURL' : 'https://simulador-de-pacientes-db11b-default-rtdb.firebaseio.com/'})
firebaseConfig = {
                'apiKey': "AIzaSyBseJ6HAiHJva-_e5wPPSkOTao1hfk6CMQ",
                'authDomain': "simulador-de-pacientes-db11b.firebaseapp.com",
                'databaseURL': "https://simulador-de-pacientes-db11b-default-rtdb.firebaseio.com",
                'projectId': "simulador-de-pacientes-db11b",
                'storageBucket': "simulador-de-pacientes-db11b.appspot.com",
                'messagingSenderId': "86248963895",
                'appId': "1:86248963895:web:8b51acc07d7fba8f4a64b2",
                'measurementId': "G-CY8R97HQKR"
}
firebase = pyrebase.initialize_app(firebaseConfig)
db_consulta= firebase.database()
auth=firebase.auth()

email=""
app.secret_key = 'Gh#7LpK2&zRt@9QwXy1%'
#crear usuario
#user = auth.create_user_with_email_and_password(email, password)
#ver la informacion de la cuenta
#info = auth.get_account_info
#autenticacion con correo
#auth.send_email_verification
#envio para resetear contraseña
#auth.send_email_verification(email)
nombre =""
rol=""
login_manager = LoginManager(app)
class User(UserMixin):
    pass
def obtener_historial_formatiado():
    url_historial = "/historial_registro_de_control_de_signos_vitales/"
    print("el url es:")
    print(url_historial)
    consulta__historial = db_consulta.child(url_historial).get()
    consulta__historial = consulta__historial.val()
    # Ordenar los datos por fecha de forma descendente
    datos_ordenados = sorted(consulta__historial.items(), key=lambda x: x[1]['timestamp'], reverse=True)
    matriz_datos = []
    for nombre, datos in datos_ordenados:
        usuario=datos['usuario']
        temperatura = datos['Temperatura']
        presion_arterial = datos['Presion_arterial']
        ritmo_cardiaco = datos['Ritmo_cardiaco']
        ritmo_respiratorio = datos['ritmo_respiratorio']
        timestamp = datos.get('timestamp', '')
        
        # Separar la hora y la fecha
        fecha, hora = timestamp.split() if timestamp else ('', '')
        # Agregar los datos a la lista de listas
        matriz_datos.append([usuario, temperatura, presion_arterial, ritmo_cardiaco, ritmo_respiratorio, fecha, hora])

    # Imprimir la matriz de datos
    for fila in matriz_datos:
        print(fila)
    historial_procesado=matriz_datos
    return historial_procesado
def obtener_casos_ordenados(email):
    url_consulta = "/casos_creados/" + email
    consulta_1 = db_consulta.child(url_consulta).get()
    consulta_simulacion = consulta_1.val()
    casos_ordenados = []

    if consulta_simulacion is None:
        print("No hay datos de casos para el usuario con email:", email)
        return []

    for caso, datos in consulta_simulacion.items():
        fecha_caso = datetime.datetime.strptime(datos['timestamp'], '%Y-%m-%d %H:%M:%S')
        casos_ordenados.append((caso, datos, fecha_caso))

    casos_ordenados.sort(key=lambda x: x[2], reverse=True)
    casos_ordenados_formateados = []

    for caso in casos_ordenados:
        nombre_caso = caso[0]
        datos_caso = caso[1]
        fecha_caso = caso[2]
        temperatura = datos_caso.get('Temperatura', '')
        presion_arterial = datos_caso.get('Presion_arterial', '')
        ritmo_cardiaco = datos_caso.get('Ritmo_cardiaco', '')
        ritmo_respiratorio = datos_caso.get('ritmo_respiratorio', '')
        fecha = fecha_caso.strftime('%Y-%m-%d')
        hora = fecha_caso.strftime('%H:%M:%S')
        casos_ordenados_formateados.append((nombre_caso.replace('_', ' '), temperatura, presion_arterial, ritmo_cardiaco, ritmo_respiratorio, fecha, hora))

    return casos_ordenados_formateados
@app.route('/', methods=['GET', 'POST'])
def login():
    if ('user' in session):
        return redirect('/casos')
    else:
        if request.method == 'POST':
            print("request.method:")
            print(request.form)
            email = request.form['username']
            password = request.form['password_login']
            print("usuario:", email)
            print("contraseña:", password)
            if not email or not password:
                pass
            else:
                try:
                    # Autenticar el usuario con Firebase Authentication
                    user = auth.sign_in_with_email_and_password(email, password)
                    
                    print("user:",user)
                    session['user']= email
                    email_parts = email.split('@')
                    if len(email_parts) == 2:  # Asegurar que haya exactamente una '@'
                        user_email = email_parts[0] + '@' + email_parts[1].replace('.', '_')
                    else:
                        # Si hay más de una '@', no reemplazar nada
                        user_email = email
                    user_email=email.replace('.', '_')
                    url_info_usuario = "/usuarios/" + user_email
                    print("url_info_usuario",url_info_usuario)
                    # Obtener datos del usuario desde Firebase
                    ref = db.reference(url_info_usuario)
                    user_data = ref.get()
                    nombre = user_data.get('nombre', '')
                    rol = user_data.get('rol', '')
                    print("correo")
                    session['nombre'] = nombre
                    session['rol'] = rol
                    session['email'] = user_email
                    session['datos_anteriores']=""
                    print("nombre:", nombre)
                    print("rol:", rol)
                    print("email:", user_email)
                    return redirect('/casos')
                
                
                except Exception as e:
                    print("Error durante la autenticación:", e)
    return render_template("login.html")
@app.route('/casos', methods=['GET', 'POST'])
@login_manager.user_loader
def casos():
    
    if ('user' in session):
        
        nombre = session['nombre']
        rol = session['rol']
        consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
        consulta_simulacion = consulta_1.val()
        # Itera sobre el diccionario y asigna cada valor a una variable correspondiente
        for key, value in consulta_simulacion.items():
            if key == 'Presion_arterial':
                presion_arterial = value
            elif key == 'Ritmo_cardiaco':
                ritmo_cardiaco = value
            elif key == 'Temperatura':
                temperatura = value
            elif key == 'ritmo_respiratorio':
                ritmo_respiratorio = value
        # Verifica si se envió un formulario para la temperatura
        if request.method == 'POST' and 'temperatura' in request.form:
            if 'temperatura' in request.form:
                temperatura = request.form['temperatura']
                
                # Verifica si la temperatura es un valor numérico
                if temperatura.isnumeric() or (temperatura.replace(".", "", 1)).isnumeric():
                    # Convierte la temperatura a un número de punto flotante
                    temperatura = float(temperatura)
                    
                    # Verifica si la temperatura está en el rango (18 a 40)
                    if 18 <= temperatura <= 40:
                        # Haz algo con la temperatura, por ejemplo, almacenarla en una base de datos
                        print("Temperatura válida:", temperatura)
                        consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
                        consulta_simulacion = consulta_1.val()
                        print(consulta_simulacion)
                        for key, value in consulta_simulacion.items():
                            if key == 'Presion_arterial':
                                presion_arterial = value
                            elif key == 'Ritmo_cardiaco':
                                ritmo_cardiaco = value
                            elif key == 'ritmo_respiratorio':
                                ritmo_respiratorio = value
                        data_enviar_control = {}
                        data_enviar_control['Presion_arterial'] = presion_arterial
                        data_enviar_control['Ritmo_cardiaco'] = ritmo_cardiaco
                        data_enviar_control['Temperatura'] = temperatura
                        data_enviar_control['ritmo_respiratorio'] = ritmo_respiratorio
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        data_historial = {}
                        data_historial['usuario'] = nombre
                        data_historial['Presion_arterial'] = "sin cambio"
                        data_historial['Ritmo_cardiaco'] = "sin cambio"
                        data_historial['Temperatura'] = temperatura
                        data_historial['ritmo_respiratorio'] = "sin cambio"
                        data_historial['timestamp'] = str(timestamp)

                        
                        # Obtiene una referencia a la base de datos
                        ref = db.reference("/control_de_signos_vitales")
                        # Utiliza la referencia para establecer los datos
                        ref.set(data_enviar_control)
                        ref = db.reference('/historial_registro_de_control_de_signos_vitales')
                        ref.push(data_historial)                     
                    else:
                        print("Temperatura fuera de rango")
                else:
                    print("Temperatura no es un número válido")
        # Verifica si se envió un formulario para la presion arterial
        if request.method == 'POST' and 'presion-arterial' in request.form:
            presion_arterial = request.form['presion-arterial']
            
            # Asegúrate de que la presión arterial tenga el formato correcto (por ejemplo, "120/80").
            if not re.match(r'^\d{2,3}/\d{2,3}$', presion_arterial):
                print("Formato incorrecto de presión arterial:", presion_arterial)
            else:
                sistolica, diastolica = map(int, presion_arterial.split('/'))
                
                # Realiza la verificación del rango para la presión arterial.
                if not (90 <= sistolica <= 120 and 60 <= diastolica <= 80):
                    print("Presión arterial fuera de rango:", presion_arterial)
                else:
                    # Si la validación es exitosa, imprime la presión arterial.
                    print("Presión arterial:", presion_arterial)

                    consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
                    consulta_simulacion = consulta_1.val()
                    # Itera sobre el diccionario y asigna cada valor a una variable correspondiente
                    for key, value in consulta_simulacion.items():
                        if key == 'Ritmo_cardiaco':
                            ritmo_cardiaco = value
                        elif key == 'Temperatura':
                            temperatura = value
                        elif key == 'ritmo_respiratorio':
                            ritmo_respiratorio = value
                    data_enviar_control = {}
                    data_enviar_control['Presion_arterial'] = presion_arterial
                    data_enviar_control['Ritmo_cardiaco'] = ritmo_cardiaco
                    data_enviar_control['Temperatura'] = temperatura
                    data_enviar_control['ritmo_respiratorio'] = ritmo_respiratorio
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    data_historial = {}
                    data_historial['usuario'] = nombre
                    data_historial['Presion_arterial'] = presion_arterial
                    data_historial['Ritmo_cardiaco'] = "sin cambio"
                    data_historial['Temperatura'] = "sin cambio"
                    data_historial['ritmo_respiratorio'] = "sin cambio"
                    data_historial['timestamp'] = str(timestamp)

                    # Obtiene una referencia a la base de datos
                    ref = db.reference("/control_de_signos_vitales")
                    # Utiliza la referencia para establecer los datos
                    ref.set(data_enviar_control)
                    ref = db.reference('/historial_registro_de_control_de_signos_vitales')
                    ref.push(data_historial)     
        # Verifica si se envió un formulario para el ritmo cardíaco
        if request.method == 'POST' and 'ritmo-cardiaco' in request.form:
            ritmo_cardiaco = request.form['ritmo-cardiaco']
                
            # Realiza la validación del ritmo cardíaco aquí
            if ritmo_cardiaco:
                ritmo_cardiaco = int(ritmo_cardiaco)  # Convierte el valor en un entero (puedes ajustar el tipo según tus necesidades)
                if 60 <= ritmo_cardiaco <= 150:
                    # El valor del ritmo cardíaco está dentro del rango deseado, puedes hacer algo con él
                    print("Ritmo Cardiaco:", ritmo_cardiaco)

                    consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
                    consulta_simulacion = consulta_1.val()

                    # Itera sobre el diccionario y asigna cada valor a una variable correspondiente
                    for key, value in consulta_simulacion.items():
                        if key == 'Presion_arterial':
                            presion_arterial = value
                        elif key == 'Temperatura':
                            temperatura = value
                        elif key == 'ritmo_respiratorio':
                            ritmo_respiratorio = value

                    data_enviar_control = {}
                    data_enviar_control['Presion_arterial'] = presion_arterial
                    data_enviar_control['Ritmo_cardiaco'] = ritmo_cardiaco
                    data_enviar_control['Temperatura'] = temperatura
                    data_enviar_control['ritmo_respiratorio'] = ritmo_respiratorio
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    data_historial = {}
                    data_historial['usuario'] = nombre
                    data_historial['Presion_arterial'] = "sin cambio"
                    data_historial['Ritmo_cardiaco'] = ritmo_cardiaco
                    data_historial['Temperatura'] = "sin cambio"
                    data_historial['ritmo_respiratorio'] = "sin cambio"
                    data_historial['timestamp'] = str(timestamp)

                    # Obtiene una referencia a la base de datos
                    ref = db.reference("/control_de_signos_vitales")
                    # Utiliza la referencia para establecer los datos
                    ref.set(data_enviar_control)
                    ref = db.reference('/historial_registro_de_control_de_signos_vitales')
                    ref.push(data_historial)  
                else:
                    # El valor está fuera del rango deseado, puedes manejarlo apropiadamente
                       print("Ritmo Cardiaco fuera de rango:", ritmo_cardiaco)
            else:
                # El campo estaba vacío
                print("El campo de ritmo cardíaco estaba vacío")
        # Verifica si se envió un formulario para el ritmo respiratorio
        if request.method == 'POST' and 'ritmo-respiratorio' in request.form:
            ritmo_respiratorio = request.form['ritmo-respiratorio']
            # Realiza la validación del ritmo respiratorio aquí
            if ritmo_respiratorio:
                ritmo_respiratorio = float(ritmo_respiratorio)  # Convierte el valor en un número de punto flotante (ajusta según tus necesidades)
                if 12 <= ritmo_respiratorio <= 35:
                    # El valor del ritmo respiratorio está dentro del rango deseado, puedes hacer algo con él
                    print("Ritmo Respiratorio:", ritmo_respiratorio)
                    consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
                    consulta_simulacion = consulta_1.val()

                    # Itera sobre el diccionario y asigna cada valor a una variable correspondiente
                    for key, value in consulta_simulacion.items():
                        if key == 'Presion_arterial':
                            presion_arterial = value
                        elif key == 'Ritmo_cardiaco':
                            ritmo_cardiaco = value
                        elif key == 'Temperatura':
                            temperatura = value

                    data_enviar_control = {}
                    data_enviar_control['Presion_arterial'] = presion_arterial
                    data_enviar_control['Ritmo_cardiaco'] = ritmo_cardiaco
                    data_enviar_control['Temperatura'] = temperatura
                    data_enviar_control['ritmo_respiratorio'] = ritmo_respiratorio
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    data_historial = {}
                    data_historial['usuario'] = nombre
                    data_historial['Presion_arterial'] = "sin cambio"
                    data_historial['Ritmo_cardiaco'] = "sin cambio"
                    data_historial['Temperatura'] = "sin cambio"
                    data_historial['ritmo_respiratorio'] = ritmo_respiratorio
                    data_historial['timestamp'] = str(timestamp)

                    # Obtiene una referencia a la base de datos
                    ref = db.reference("/control_de_signos_vitales")
                    # Utiliza la referencia para establecer los datos
                    ref.set(data_enviar_control)
                    ref = db.reference('/historial_registro_de_control_de_signos_vitales')
                    ref.push(data_historial)  
                else:
                    # El valor está fuera del rango deseado, puedes manejarlo apropiadamente
                    print("Ritmo Respiratorio fuera de rango:", ritmo_respiratorio)
            else:
                # El campo estaba vacío
                print("El campo de ritmo respiratorio estaba vacío")
        if request.method == 'POST' and 'simular-caso' in request.form:
            # Verificar si 'selected-case' está presente en el formulario
            if 'selected-case' in request.form:
                selected_case = request.form['selected-case'].strip()
                print("304")
                selected_case = selected_case.replace(" ", "_")
                print("Caso seleccionado:", selected_case)
                print("306")
                selected_case = selected_case.lower()
                url_cosulta ="/casos_estandar" +"/"+selected_case
                consulta_1 = db_consulta.child(url_cosulta).get()
                consulta_simulacion = consulta_1.val()
                print(consulta_simulacion)
                for key, value in consulta_simulacion.items():
                    if key == 'Presion_arterial':
                        presion_arterial = value
                    elif key == 'Ritmo_cardiaco':
                        ritmo_cardiaco = value
                    elif key == 'Temperatura':
                        temperatura = value
                    elif key == 'ritmo_respiratorio':
                        ritmo_respiratorio = value
                    data_enviar_control = {}
                    data_enviar_control['Presion_arterial'] = presion_arterial
                    data_enviar_control['Ritmo_cardiaco'] = ritmo_cardiaco
                    data_enviar_control['Temperatura'] = temperatura
                    data_enviar_control['ritmo_respiratorio'] = ritmo_respiratorio
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    data_historial = {}
                    data_historial['usuario'] = nombre
                    data_historial['Presion_arterial'] = presion_arterial
                    data_historial['Ritmo_cardiaco'] = ritmo_cardiaco
                    data_historial['Temperatura'] = temperatura
                    data_historial['ritmo_respiratorio'] = ritmo_respiratorio
                    data_historial['timestamp'] = str(timestamp)
                    # Obtiene una referencia a la base de datos
                    ref = db.reference("/control_de_signos_vitales")
                    # Utiliza la referencia para establecer los datos
                    ref.set(data_enviar_control)
                    ref = db.reference('/historial_registro_de_control_de_signos_vitales')
                    ref.push(data_historial)  
            else:
                # Si 'selected-case' no está presente en el formulario, manejar el error apropiadamente
                print("Error: No se encontró 'selected-case' en el formulario.")
        return render_template("casos.html", nombre=nombre, rol=rol, presion_arterial=presion_arterial, ritmo_cardiaco=ritmo_cardiaco, temperatura=temperatura, ritmo_respiratorio=ritmo_respiratorio)
    else:
        return redirect('/')
@app.route('/crear_casos',methods=['GET', 'POST'])
@login_manager.user_loader
def crear_casos():

    if ('user' in session):
        nombre = session['nombre']
        rol = session['rol']
        email =session['email']
        datos_anteriores=session['datos_anteriores']
        print("datos_anteriores:")
        print(datos_anteriores)
        print("nombre: ",nombre)
        print("rol: ",rol)
        print("email: ",email)
        presion_arterial_s=""
        ritmo_cardiaco_s=""
        temperatura_s=""
        ritmo_respiratorio_s=""
        temperatura_s=""
        consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
        consulta_simulacion = consulta_1.val()
        # Itera sobre el diccionario y asigna cada valor a una variable correspondiente
        for key, value in consulta_simulacion.items():
            if key == 'Presion_arterial':
                presion_arterial_s = value
            elif key == 'Ritmo_cardiaco':
                ritmo_cardiaco_s = value
            elif key == 'Temperatura':
                temperatura_s = value
            elif key == 'ritmo_respiratorio':
                ritmo_respiratorio_s = value
            #extaer la lista de casos 
        casos = obtener_casos_ordenados(email)
        if request.method == 'POST' and 'simular-caso-creado' in request.form:
            print("Se ha enviado el formulario de simulación de caso")
            nombre_caso = request.form.get('nombre-caso', '')  # Obtener el valor de 'nombre-caso' del formulario
            print("El nombre del caso es:", nombre_caso)  # Imprimir el valor de nombre_caso
        if request.method == 'POST' and isinstance(request.form, ImmutableMultiDict):
            print("Se ha enviado el formulario de creación de casos")
            print("linea 428 request.form:")
            print(request.form)
            if 'temperatura-crear' in request.form:
                temperatura = request.form['temperatura-crear']
                presion_arterial = request.form['presion-arterial-crear']
                ritmo_cardiaco = request.form['ritmo-cardiaco-crear']
                ritmo_respiratorio = request.form['ritmo-respiratorio-crear']
                nombre_caso = request.form.get('nombre-caso', '')
                if nombre_caso.isspace():
                    print("el nombre del caso no pede tener solo espacios")
                    nombre_caso_error='El nombre del caso no puede tener solo espacios'
                    request.form = {}
                    casos = obtener_casos_ordenados(email)

                    return render_template('crear_casos.html', nombre=nombre, rol=rol, nombre_caso_error=nombre_caso_error,
                                                    temperatura=temperatura, presion_arterial=presion_arterial,
                                                    ritmo_cardiaco=ritmo_cardiaco, ritmo_respiratorio=ritmo_respiratorio,
                                                    nombre_caso=nombre_caso,casos=casos,temperatura_s=temperatura_s, presion_arterial_s=presion_arterial_s,
                                                    ritmo_cardiaco_s=ritmo_cardiaco_s, ritmo_respiratorio_s=ritmo_respiratorio_s)
                else:
                    if nombre_caso != '':
                        nombre_caso = nombre_caso.lower().replace(' ', '_')
                        print("Temperatura:", temperatura)
                        print("Presión arterial:", presion_arterial)
                        print("Ritmo cardíaco:", ritmo_cardiaco)
                        print("Ritmo respiratorio:", ritmo_respiratorio)
                        print("Nombre del caso:", nombre_caso)
                        url_consulta ="/casos_creados/" + email
                        print("enlace: ",url_consulta)
                        consulta_1 = db_consulta.child(url_consulta).get()
                        consulta_simulacion = consulta_1.val()
                        print(consulta_simulacion)
                        if consulta_simulacion is None:
                            if nombre_caso =="":
                                print("se va a crear el caso con nombre:"+ nombre_caso)
                                url_envio = "/casos_creados/" + email + "/" + nombre_caso
                                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                data_enviar_caso_creado = {}
                                data_enviar_caso_creado['Presion_arterial'] = presion_arterial
                                data_enviar_caso_creado['Ritmo_cardiaco'] = ritmo_cardiaco
                                data_enviar_caso_creado['Temperatura'] = temperatura
                                data_enviar_caso_creado['ritmo_respiratorio'] = ritmo_respiratorio
                                data_enviar_caso_creado['timestamp'] = str(timestamp)
                                # Obtiene una referencia a la base de datos
                                ref = db.reference(url_envio)
                                # Utiliza la referencia para establecer los datos
                                ref.set(data_enviar_caso_creado)
                                nombre_caso=""
                                consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
                                consulta_simulacion = consulta_1.val()
                                # Itera sobre el diccionario y asigna cada valor a una variable correspondiente
                                for key, value in consulta_simulacion.items():
                                    if key == 'Presion_arterial':
                                        presion_arterial_s = value
                                    elif key == 'Ritmo_cardiaco':
                                        ritmo_cardiaco_s = value
                                    elif key == 'Temperatura':
                                        temperatura_s = value
                                    elif key == 'ritmo_respiratorio':
                                        ritmo_respiratorio_s = value
                                casos = obtener_casos_ordenados(email)
                                return render_template('crear_casos.html',nombre=nombre, rol=rol,nombre_caso=nombre_caso,casos=casos,
                                                        presion_arterial_s=presion_arterial_s,ritmo_cardiaco_s=ritmo_cardiaco_s,
                                                        temperatura_s=temperatura_s,ritmo_respiratorio_s=ritmo_respiratorio_s)
                            else:
                                print("se va a crear el caso con nombre:"+ nombre_caso)
                                url_envio = "/casos_creados/" + email + "/" + nombre_caso
                                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                data_enviar_caso_creado = {}
                                data_enviar_caso_creado['Presion_arterial'] = presion_arterial
                                data_enviar_caso_creado['Ritmo_cardiaco'] = ritmo_cardiaco
                                data_enviar_caso_creado['Temperatura'] = temperatura
                                data_enviar_caso_creado['ritmo_respiratorio'] = ritmo_respiratorio
                                data_enviar_caso_creado['timestamp'] = str(timestamp)
                                # Obtiene una referencia a la base de datos
                                ref = db.reference(url_envio)
                                # Utiliza la referencia para establecer los datos
                                ref.set(data_enviar_caso_creado)
                                nombre_caso=""
                                consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
                                consulta_simulacion = consulta_1.val()
                                # Itera sobre el diccionario y asigna cada valor a una variable correspondiente
                                for key, value in consulta_simulacion.items():
                                    if key == 'Presion_arterial':
                                        presion_arterial_s = value
                                    elif key == 'Ritmo_cardiaco':
                                        ritmo_cardiaco_s = value
                                    elif key == 'Temperatura':
                                        temperatura_s = value
                                    elif key == 'ritmo_respiratorio':
                                        ritmo_respiratorio_s = value
                                casos = obtener_casos_ordenados(email)
                                return render_template('crear_casos.html',nombre=nombre, rol=rol,nombre_caso=nombre_caso,casos=casos,
                                                        presion_arterial_s=presion_arterial_s,ritmo_cardiaco_s=ritmo_cardiaco_s,
                                                        temperatura_s=temperatura_s,ritmo_respiratorio_s=ritmo_respiratorio_s)
                        else: 
                            # Verificar si el nombre del caso ya existe en Firebase
                            if nombre_caso is not None:
                                consulta_1 = db_consulta.child(url_consulta).get()
                                consultas_simulacion = consulta_1.val()
                                
                                # Verificar si el nombre del caso ya existe en las consultas de Firebase
                                if nombre_caso in consultas_simulacion:
                                    print("ya hiciste el caso")
                                    nombre_caso_error='El nombre del caso'+ '(' + nombre_caso +')'+ ' ya existe. Por favor, elige otro nombre.'
                                    consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
                                    consulta_simulacion = consulta_1.val()
                                    # Itera sobre el diccionario y asigna cada valor a una variable correspondiente
                                    for key, value in consulta_simulacion.items():
                                        if key == 'Presion_arterial':
                                            presion_arterial_s = value
                                        elif key == 'Ritmo_cardiaco':
                                            ritmo_cardiaco_s = value
                                        elif key == 'Temperatura':
                                            temperatura_s = value
                                        elif key == 'ritmo_respiratorio':
                                            ritmo_respiratorio_s = value
                                    casos = obtener_casos_ordenados(email)
                                    datos_anteriores = request.form
                                    print("datos_anteriores linea 513")
                                    print(datos_anteriores)
                                    session['datos_anteriores']= datos_anteriores
                                    nombre_caso_error=""
                                    nombre_caso=""
                                    return render_template('crear_casos.html', nombre=nombre, rol=rol, nombre_caso_error=nombre_caso_error,
                                                        temperatura_s=temperatura_s, presion_arterial_s=presion_arterial_s,
                                                        ritmo_cardiaco_s=ritmo_cardiaco_s, ritmo_respiratorio_s=ritmo_respiratorio_s,
                                                        casos=casos,nombre_caso="")
                                else:
                                    
                                    print("se va a crear el caso con nombre:"+ nombre_caso)
                                    url_envio = "/casos_creados/" + email + "/" + nombre_caso
                                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    data_enviar_caso_creado = {}
                                    data_enviar_caso_creado['Presion_arterial'] = presion_arterial
                                    data_enviar_caso_creado['Ritmo_cardiaco'] = ritmo_cardiaco
                                    data_enviar_caso_creado['Temperatura'] = temperatura
                                    data_enviar_caso_creado['ritmo_respiratorio'] = ritmo_respiratorio
                                    data_enviar_caso_creado['timestamp'] = str(timestamp)
                                    # Obtiene una referencia a la base de datos
                                    ref = db.reference(url_envio)
                                    # Utiliza la referencia para establecer los datos
                                    ref.set(data_enviar_caso_creado)
                                    nombre_caso=""
                                    consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
                                    consulta_simulacion = consulta_1.val()
                                    # Itera sobre el diccionario y asigna cada valor a una variable correspondiente
                                    for key, value in consulta_simulacion.items():
                                        if key == 'Presion_arterial':
                                            presion_arterial_s = value
                                        elif key == 'Ritmo_cardiaco':
                                            ritmo_cardiaco_s = value
                                        elif key == 'Temperatura':
                                            temperatura_s = value
                                        elif key == 'ritmo_respiratorio':
                                            ritmo_respiratorio_s = value
                                    casos = obtener_casos_ordenados(email)
                                    return render_template('crear_casos.html',nombre=nombre, rol=rol,nombre_caso=nombre_caso,casos=casos,
                                                        presion_arterial_s=presion_arterial_s,ritmo_cardiaco_s=ritmo_cardiaco_s,
                                                        temperatura_s=temperatura_s,ritmo_respiratorio_s=ritmo_respiratorio_s)
                    else:
                        datos_anteriores = session['datos_anteriores']
                        print("datos anteriores")
                        print(datos_anteriores)
                        datos_formulario = request.form
                        datos_formulario = dict(datos_formulario)
                        datos_anteriores_dict = dict(datos_anteriores)
                        print(datos_anteriores_dict)

                        if datos_formulario == datos_anteriores_dict:
                            print("Los datos enviados son iguales a los anteriores")
                            casos = obtener_casos_ordenados(email)
                            return render_template('crear_casos.html',nombre=nombre, rol=rol,nombre_caso=nombre_caso,casos=casos,
                                                   presion_arterial_s=presion_arterial_s,ritmo_cardiaco_s=ritmo_cardiaco_s,
                                                   temperatura_s=temperatura_s,ritmo_respiratorio_s=ritmo_respiratorio_s)
                        else:
                            print("son diferentes")
                            print("se va crear un caso colocandole un nombre estandar")
                            url_consulta ="/casos_creados/" + email
                            print("enlace: ",url_consulta)
                            caso_base = "caso_"
                            num_caso = 1
                            consulta_1 = db_consulta.child(url_consulta).get()
                            consulta_simulacion = consulta_1.val()
                            print(consulta_simulacion)
                            if consulta_simulacion is None:
                                if nombre_caso != "":
                                    print("Se creará el caso con el nombre:", nombre_caso)
                                    nombre_caso= "caso_1"
                                    url_envio = "/casos_creados/" + email + "/" + nombre_caso
                                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    data_enviar_caso_creado = {}
                                    data_enviar_caso_creado['Presion_arterial'] = presion_arterial
                                    data_enviar_caso_creado['Ritmo_cardiaco'] = ritmo_cardiaco
                                    data_enviar_caso_creado['Temperatura'] = temperatura
                                    data_enviar_caso_creado['ritmo_respiratorio'] = ritmo_respiratorio
                                    data_enviar_caso_creado['timestamp'] = str(timestamp)
                                    # Obtiene una referencia a la base de datos
                                    ref = db.reference(url_envio)
                                    # Utiliza la referencia para establecer los datos
                                    ref.set(data_enviar_caso_creado)
                                    nombre_caso= ""
                                    request.form = {}
                                    nombre_caso_error=""
                                    temperatura=""
                                    presion_arterial=""
                                    ritmo_cardiaco=""
                                    ritmo_respiratorio=""
                                    nombre_caso=""
                                    datos_anteriores = request.form
                                    print("datos_anteriores linea 513")
                                    print(datos_anteriores)
                                    session['datos_anteriores']= datos_anteriores
                                    consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
                                    consulta_simulacion = consulta_1.val()
                                    # Itera sobre el diccionario y asigna cada valor a una variable correspondiente
                                    for key, value in consulta_simulacion.items():
                                        if key == 'Presion_arterial':
                                            presion_arterial_s = value
                                        elif key == 'Ritmo_cardiaco':
                                            ritmo_cardiaco_s = value
                                        elif key == 'Temperatura':
                                            temperatura_s = value
                                        elif key == 'ritmo_respiratorio':
                                            ritmo_respiratorio_s = value
                                    #actualizar tabla:
                                    #extaer la lista de casos 
                                    casos = obtener_casos_ordenados(email)
                                    return render_template('crear_casos.html', nombre=nombre, rol=rol, nombre_caso_error=nombre_caso_error,
                                                        temperatura_s=temperatura_s, presion_arterial_s=presion_arterial,
                                                        ritmo_cardiaco_s=ritmo_cardiaco, ritmo_respiratorio_s=ritmo_respiratorio_s,
                                                            nombre_caso=nombre_caso,casos=casos)
                                else:
                                    print("Se creará el caso con el nombre:", nombre_caso)
                                    url_envio = "/casos_creados/" + email + "/" + nombre_caso
                                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    data_enviar_caso_creado = {}
                                    data_enviar_caso_creado['Presion_arterial'] = presion_arterial
                                    data_enviar_caso_creado['Ritmo_cardiaco'] = ritmo_cardiaco
                                    data_enviar_caso_creado['Temperatura'] = temperatura
                                    data_enviar_caso_creado['ritmo_respiratorio'] = ritmo_respiratorio
                                    data_enviar_caso_creado['timestamp'] = str(timestamp)
                                    # Obtiene una referencia a la base de datos
                                    ref = db.reference(url_envio)
                                    # Utiliza la referencia para establecer los datos
                                    ref.set(data_enviar_caso_creado)
                                    nombre_caso= ""
                                    request.form = {}
                                    nombre_caso_error=""
                                    temperatura=""
                                    presion_arterial=""
                                    ritmo_cardiaco=""
                                    ritmo_respiratorio=""
                                    nombre_caso=""
                                    datos_anteriores = request.form
                                    print("datos_anteriores linea 513")
                                    print(datos_anteriores)
                                    session['datos_anteriores']= datos_anteriores
                                    consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
                                    consulta_simulacion = consulta_1.val()
                                    # Itera sobre el diccionario y asigna cada valor a una variable correspondiente
                                    for key, value in consulta_simulacion.items():
                                        if key == 'Presion_arterial':
                                            presion_arterial_s = value
                                        elif key == 'Ritmo_cardiaco':
                                            ritmo_cardiaco_s = value
                                        elif key == 'Temperatura':
                                            temperatura_s = value
                                        elif key == 'ritmo_respiratorio':
                                            ritmo_respiratorio_s = value
                                    #actualizar tabla:
                                    #extaer la lista de casos 
                                    casos = obtener_casos_ordenados(email)
                                    return render_template('crear_casos.html', nombre=nombre, rol=rol, nombre_caso_error=nombre_caso_error,
                                                        temperatura_s=temperatura_s, presion_arterial_s=presion_arterial,
                                                        ritmo_cardiaco_s=ritmo_cardiaco, ritmo_respiratorio_s=ritmo_respiratorio_s,
                                                            nombre_caso=nombre_caso,casos=casos)
                            else:
                                while True:
                                    nombre_caso = caso_base + str(num_caso)
                                    
                                    # Verifica si el nombre del caso ya existe en Firebase
                                    if nombre_caso in consulta_simulacion:
                                        num_caso += 1
                                    else:
                                        # Cuando encuentra un nombre de caso que no está en uso, sal del bucle
                                        break
                                # Ahora tienes el primer nombre de caso disponible que no está repetido
                                print("Se creará el caso con el nombre:", nombre_caso)
                                url_envio = "/casos_creados/" + email + "/" + nombre_caso
                                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                data_enviar_caso_creado = {}
                                data_enviar_caso_creado['Presion_arterial'] = presion_arterial
                                data_enviar_caso_creado['Ritmo_cardiaco'] = ritmo_cardiaco
                                data_enviar_caso_creado['Temperatura'] = temperatura
                                data_enviar_caso_creado['ritmo_respiratorio'] = ritmo_respiratorio
                                data_enviar_caso_creado['timestamp'] = str(timestamp)
                                # Obtiene una referencia a la base de datos
                                ref = db.reference(url_envio)
                                # Utiliza la referencia para establecer los datos
                                ref.set(data_enviar_caso_creado)
                                nombre_caso= ""
                                session['datos_anteriores']=request.form
                                datosguardados = session['datos_anteriores']
                                print("linea 548")
                                print(datosguardados)
                                casos=obtener_casos_ordenados(email)
                                return render_template('crear_casos.html',nombre=nombre, rol=rol,nombre_caso=nombre_caso,casos=casos)

            else:
                print("no tiene la variable temperatura")
                print("tiene la variable caso-simular")
                request_form_dict = dict(request.form.to_dict())
                print("request_form_dict: ")
                print(request_form_dict)
                if 'caso-simular' in request.form:
                    if request_form_dict == datos_anteriores:
                        print("Los diccionarios son iguales")

                    else:
                        print("Los diccionarios son diferentes")
                        #guarda el dato
                        print("se va a simular el caso:")
                        caso_simular = request.form['caso-simular'].replace(" ", "_")
                        print(caso_simular)
                        url_consulta = "/casos_creados/" + email + "/" + caso_simular
                        print("el url es:")
                        print(url_consulta)
                        consulta_1 = db_consulta.child(url_consulta).get()
                        consulta_simulacion = consulta_1.val()
                        print(consulta_simulacion)
                        for key, value in consulta_simulacion.items():
                            if key == 'Temperatura':
                                temperatura = value
                            elif key == 'Presion_arterial':
                                presion_arterial = value
                            elif key == 'Ritmo_cardiaco':
                                ritmo_cardiaco = value
                            elif key == 'ritmo_respiratorio':
                                ritmo_respiratorio = value
                        print("temperatura",temperatura)
                        print("presion_arterial",presion_arterial)
                        print("ritmo_cardiaco",ritmo_cardiaco)
                        print("ritmo_respiratorio",ritmo_respiratorio)
                        data_enviar_control = {}
                        data_enviar_control['Presion_arterial'] = presion_arterial
                        data_enviar_control['Ritmo_cardiaco'] = ritmo_cardiaco
                        data_enviar_control['Temperatura'] = temperatura
                        data_enviar_control['ritmo_respiratorio'] = ritmo_respiratorio
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        data_historial = {}
                        data_historial['usuario'] = nombre
                        data_historial['Presion_arterial'] = presion_arterial
                        data_historial['Ritmo_cardiaco'] = ritmo_cardiaco
                        data_historial['Temperatura'] = temperatura
                        data_historial['ritmo_respiratorio'] = ritmo_respiratorio
                        data_historial['timestamp'] = str(timestamp)

                        print("linea 636")
                        # Obtiene una referencia a la base de datos
                        ref = db.reference("/control_de_signos_vitales/")
                        # Utiliza la referencia para establecer los datos
                        print("data_enviar_control")
                        print(data_enviar_control)
                        ref.set(data_enviar_control)
                        ref = db.reference('/historial_registro_de_control_de_signos_vitales')
                        ref.push(data_historial)     
                        datos_anteriores =request.form
                        session['datos_anteriores']= datos_anteriores
                        nombre_caso=""
                        consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
                        consulta_simulacion = consulta_1.val()
                        # Itera sobre el diccionario y asigna cada valor a una variable correspondiente
                        for key, value in consulta_simulacion.items():
                            if key == 'Presion_arterial':
                                presion_arterial_s = value
                            elif key == 'Ritmo_cardiaco':
                                ritmo_cardiaco_s = value
                            elif key == 'Temperatura':
                                temperatura_s = value
                            elif key == 'ritmo_respiratorio':
                                ritmo_respiratorio_s = value
                        return render_template('crear_casos.html',nombre=nombre, rol=rol,nombre_caso=nombre_caso,casos=casos,temperatura_s=temperatura_s, presion_arterial_s=presion_arterial_s,
                                                    ritmo_cardiaco_s=ritmo_cardiaco_s, ritmo_respiratorio_s=ritmo_respiratorio_s)
                                                                        
                else:
                    print("no tiene la variable caso-simular")
                    if 'caso-eliminar' in request.form:
                        if request_form_dict == datos_anteriores:
                            print("Los diccionarios son iguales")
                            nombre_caso=""
                            consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
                            consulta_simulacion = consulta_1.val()
                            for key, value in consulta_simulacion.items():
                                if key == 'Presion_arterial':
                                    presion_arterial_s = value
                                elif key == 'Ritmo_cardiaco':
                                    ritmo_cardiaco_s = value
                                elif key == 'Temperatura':
                                    temperatura_s = value
                                elif key == 'ritmo_respiratorio':
                                    ritmo_respiratorio_s = value
                            return render_template('crear_casos.html',nombre=nombre, rol=rol,nombre_caso=nombre_caso,casos=casos,temperatura_s=temperatura_s, presion_arterial_s=presion_arterial_s,
                                                    ritmo_cardiaco_s=ritmo_cardiaco_s, ritmo_respiratorio_s=ritmo_respiratorio_s)
                        else:
                            print("Los diccionarios son diferentes")
                            #guarda el dato
                            print("se va a eliminar el caso:")
                            print(request.form)
                            caso_eliminar = request.form['caso-eliminar'].replace(" ", "_")
                            url_caso_eliminar ="/casos_creados/" + email + "/" + caso_eliminar
                            print("url_caso_eliminar:")
                            print(url_caso_eliminar)
                            ref = db.reference(url_caso_eliminar)
                            ref.delete()
                            consulta_1 = db_consulta.child("/control_de_signos_vitales").get()
                            consulta_simulacion = consulta_1.val()
                            # Itera sobre el diccionario y asigna cada valor a una variable correspondiente
                            for key, value in consulta_simulacion.items():
                                if key == 'Presion_arterial':
                                    presion_arterial_s = value
                                elif key == 'Ritmo_cardiaco':
                                    ritmo_cardiaco_s = value
                                elif key == 'Temperatura':
                                    temperatura_s = value
                                elif key == 'ritmo_respiratorio':
                                        ritmo_respiratorio_s = value
                            datos_anteriores =request.form
                            session['datos_anteriores']= datos_anteriores
                            nombre_caso=""
                            casos=obtener_casos_ordenados(email)
                            return render_template('crear_casos.html',nombre=nombre, rol=rol,nombre_caso=nombre_caso,casos=casos,
                                                   temperatura_s=temperatura_s, presion_arterial_s=presion_arterial_s,
                                                   ritmo_cardiaco_s=ritmo_cardiaco_s, ritmo_respiratorio_s=ritmo_respiratorio_s)
                    else:
                        print("no tiene la variable caso-eliminar")
                        
        nombre_caso= ""
        return render_template('crear_casos.html',nombre=nombre, rol=rol,nombre_caso=nombre_caso,casos=casos,temperatura_s=temperatura_s, presion_arterial_s=presion_arterial_s,
                                                    ritmo_cardiaco_s=ritmo_cardiaco_s, ritmo_respiratorio_s=ritmo_respiratorio_s)
    else:
        return redirect('/')
@app.route('/historial')
@login_manager.user_loader
def historial():
    if ('user' in session):
        nombre = session['nombre']
        rol = session['rol']
        print("nombre: ",nombre)
        print("rol: ",rol)
        historial_procesado = obtener_historial_formatiado()
        return render_template('historial.html', nombre=nombre, rol=rol,casos= historial_procesado)
    else:
        return redirect('/')
@app.route('/evaluacion',methods=['GET', 'POST'])
@login_manager.user_loader
def evaluacion():
    if ('user' in session):
        nombre = session['nombre']
        rol = session['rol']
        print("nombre:",nombre)
        print("rol:",rol)
        if request.method == 'POST':
            print(request.form)
            # Obtener el PIN enviado desde el frontend
            pin = request.form['pin-2']
            print("PIN recibido:", pin)
            # Aquí puedes agregar la lógica para manejar el PIN recibido
        return render_template('evaluacion.html',nombre=nombre, rol=rol)
    else:
        return redirect('/')
@app.route('/informacion')
@login_manager.user_loader
def informacion():
    if ('user' in session):
        nombre = session['nombre']
        rol = session['rol']
        return render_template('informacion.html', nombre=nombre, rol=rol)
    else:
        return redirect('/')
@app.route('/logout')
@login_manager.user_loader
def logout():
    if ('user' in session):
        # Cerrar sesión en Firebase
        # Limpiar sesión

        auth.current_user = None
        session.pop('user')
        session.pop('nombre')
        session.pop('rol')
        return redirect('/')
    
    return redirect('/')
@app.route('/registro',methods=['GET', 'POST'])
def registro():
    if 'user' in session:
        # Si el usuario ya ha iniciado sesión, redirige a la página principal o a otra página
        return redirect('/casos')
    else:
        if request.method == 'POST':
            print("request.form:")
            print(request.form)
            # Se ha enviado un formulario POST, así que procesa los datos del formulario
            username = request.form['username_registro']
            email = request.form['email_registro']
            password = request.form['password_registro']
            role = request.form['role_registro']
            license_code = request.form.get('license_registro', '')  # En caso de que no se envíe un código de licencia
            print("Nombre de usuario:", username)
            print("Correo electrónico:", email)
            print("Contraseña:", password)
            print("Rol:", role)
            print("Código de licencia:", license_code)
            try:
                auth_token = auth.create_user_with_email_and_password(email, password)
                token_id = auth_token['idToken']
                verificacion = auth.send_email_verification(token_id)
                print(verificacion)
                if 'email' in verificacion:    
                    correo = email.replace('.', '_')
                    print("email modificado")
                    print(correo)
                    url_envio = "/usuarios/" + correo + "/"  
                    data_crear_datos_usuario = {}
                    data_crear_datos_usuario['nombre'] = username
                    data_crear_datos_usuario['rol'] = role
                    # Obtiene una referencia a la base de datos
                    ref = db.reference(url_envio)
                    ref.set(data_crear_datos_usuario)
                    # Redirige a la página de inicio de sesión u otra página según sea necesario
                    return redirect('/')
            except Exception as e:
                # Si ocurre algún error durante el registro
                print("Error durante el registro:", e)
                # Una vez que hayas procesado los datos del formulario, se redirige a la pagina
                return render_template('registro.html')
        return render_template('registro.html')
if __name__ == '__main__':
    #para hacer pruebas y ver cambios al instante
    app.run(debug=True,port=8080)
    #para conectarsede otro dispositivo
    #app.run(host='0.0.0.0', port=8080)
