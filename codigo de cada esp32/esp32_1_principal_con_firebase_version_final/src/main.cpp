// LIBRERIAS
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <Arduino.h>
#include <FirebaseESP32.h>
#include <ArduinoJson.h>

#define LED_wifi 2
#define pin_pulsador 4

#define FIREBASE_HOST "url de firebase"
#define FIREBASE_AUTH "clave de autenticacion"
#define DATABASE_PATH "control_de_signos_vitales/"
FirebaseData firebaseData;

const char *ssid = "simulador_pacientes";
const char *password = "simulador9507";
// const char *ssid = "redmicote";
// const char *password = "cotemaster";
const char *serverIP_temperatura = "192.168.1.101"; // Dirección IP fija del servidor
const char *serverIP_frecuencia_respiratoria = "192.168.1.102";
const char *serverIP_presion_arterial = "192.168.1.103";
const char *serverIP_frecuencia_cardiaca = "192.168.1.104";
const int udpPort = 12345; // Puerto UDP del servidor
String temperatura = "";
String frecuencia_respiratoria = "";
String presion_arterial = "";
String frecuencia_cardiaca = "";
String mensaje_respuesta = "";
int contador = 0;
int t_envio_signo = 5000;
int estadoled1 = 0;
int orden_de_envio = 0;
int contador_red = 0;
int contador_reconec = 0;
int contador_reinicio = 0;
int activar_sistema = 0;
int contador_leer_firebase_para_enviar = 0;
int estado_pulsador = 0;
int bandera_pulsador = 0;
int bandera_esperar_enviar_datos = 0;
int bandera_leer_firebase = 0;
WiFiUDP udp;

void (*resetSoftware)(void) = 0;
String extraerDato(char *datoCompleto, int tipo_signo)
{
  // Convierte el array de caracteres a un String
  String datoString = String(datoCompleto);

  // Encuentra la posición del primer '>'
  int inicio = datoString.indexOf('>');

  // Encuentra la posición del primer '<' después del '>'
  int fin = datoString.indexOf('<', inicio);

  // Extraer la parte entre > y <
  if (inicio != -1 && fin != -1)
  {
    datoString = datoString.substring(inicio + 1, fin);
    // Verificar si la cadena comienza con "temperatura:"
    mensaje_respuesta = "";
    switch (tipo_signo)
    {
    case 0:
      mensaje_respuesta = "respuesta_temperatura:";
      break;
    case 1:
      mensaje_respuesta = "respuesta_frecuencia_respiratoria:";
      break;
    case 2:
      mensaje_respuesta = "respuesta_presion_arterial:";
      break;
    case 3:
      mensaje_respuesta = "respuesta_frecuencia_cardiaca:";
      break;
    default:
      Serial.println("no se indica el tipo de valor");
      break;
    }

    if (datoString.startsWith(mensaje_respuesta))
    {
      // Encontrar la posición del primer ':'
      int inicioNumero = datoString.indexOf(':');

      // Extraer la parte después del ':'
      return datoString.substring(inicioNumero + 1);
    }
    else
    {
      // return "No se encontró la palabra clave 'respuesta_temperatura:";
      return "No se encontró la palabra clave  '%s'\n", mensaje_respuesta;
    }
  }
  else
  {
    return "No se encontraron los caracteres '><'";
  }
}
void cambiar_envio(int numero_signo_vital)
{
  switch (numero_signo_vital)
  {
  case 0:
    orden_de_envio = 1;
    break;
  case 1:
    orden_de_envio = 2;
    break;
  case 2:
    orden_de_envio = 3;
    break;
  case 3:
    orden_de_envio = 0;
    break;
  default:
    break;
  }
}
void setupWiFi()
{
  // Inicia el proceso de conexión a la red WiFi
  WiFi.begin(ssid, password);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);

  // Espera a que la conexión sea exitosa o hasta que se alcance el límite de intentos
  while ((WiFi.status() != WL_CONNECTED) && (contador_red <= 122))
  {
    delay(50);

    // Alterna el estado del LED WiFi durante el proceso de conexión
    estadoled1 = !estadoled1;
    digitalWrite(LED_wifi, estadoled1);

    Serial.print(".");
    contador_red++;
  }

  // Verifica el resultado de la conexión y muestra mensajes correspondientes
  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("No se conectó :(");
    estadoled1 = 0;
    digitalWrite(LED_wifi, estadoled1);
  }
  else
  {
    Serial.println("¡Conectado! :)");
    udp.begin(udpPort);
  }
}
void titileo_led_wifi()
{
  // Incrementa el contador de reconexión
  contador_reconec++;

  // Realiza titileo del LED WiFi en pasos específicos
  if (contador_reconec == 500 || contador_reconec == 1000 || contador_reconec == 1500 || contador_reconec == 2000 || contador_reconec == 2500)
  {
    // Alterna el estado del LED
    estadoled1 = !estadoled1;
    digitalWrite(LED_wifi, estadoled1);
  }

  // Realiza el proceso de reconexión y reinicia el contador
  if (contador_reconec == 3000)
  {
    contador_reconec = 0;
    WiFi.begin(ssid, password);
    Serial.println("Intenta Reconexión...");

    // Alterna el estado del LED antes de la reconexión
    estadoled1 = !estadoled1;
    digitalWrite(LED_wifi, estadoled1);
  }
}
void envio_signo_vital(String valor_signo_vital, int numero_signo_vital)
{
  if (contador == t_envio_signo)
  {

    switch (numero_signo_vital)
    {
    case 0:
      Serial.println("---------------------------------");
      Serial.println("");
      Serial.println("");
      Serial.println("envia temperatura");
      udp.beginPacket(serverIP_temperatura, udpPort);
      udp.print("<temperatura:" + temperatura + ">");
      udp.endPacket();
      break;
    case 1:
      Serial.println("envia frecuencia respiratoria");
      udp.beginPacket(serverIP_frecuencia_respiratoria, udpPort);
      udp.print("<frecuencia_respiratoria:" + frecuencia_respiratoria + ">");
      udp.endPacket();
      break;
    case 2:
      Serial.println("envia presion arterial");
      udp.beginPacket(serverIP_presion_arterial, udpPort);
      udp.print("<presion_arterial:" + presion_arterial + ">");
      udp.endPacket();
      break;
    case 3:
      Serial.println("envia ritmo cardiaco");
      udp.beginPacket(serverIP_frecuencia_cardiaca, udpPort);
      udp.print("<frecuencia_cardiaca:" + frecuencia_cardiaca + ">");
      udp.endPacket();
      break;
    default:
      Serial.println("no envia nada");
      break;
    }
  }
  int packetSize = udp.parsePacket();
  if (packetSize)
  {
    char incomingPacket[255];
    udp.read(incomingPacket, sizeof(incomingPacket));
    incomingPacket[packetSize] = '\0';
    String datoExtraido = extraerDato(incomingPacket, numero_signo_vital);

    // Imprimir el resultado

    switch (numero_signo_vital)
    {
    case 0:
      Serial.println("Respuesta de temperatura: " + datoExtraido);
      break;
    case 1:
      Serial.println("Respuesta de frecuencia respiratoria: " + datoExtraido);
      break;
    case 2:
      Serial.println("Respuesta de presion arterial: " + datoExtraido);
      break;
    case 3:
      Serial.println("Respuesta de frecuencia cardiaca: " + datoExtraido);
      break;
    default:
      break;
    }

    // Eliminar el último carácter
    mensaje_respuesta.remove(mensaje_respuesta.length() - 1);

    // Reemplazar los guiones bajos por espacios
    mensaje_respuesta.replace("_", " ");
    if (valor_signo_vital == datoExtraido)
    {
      Serial.println("Se confirma " + mensaje_respuesta);
      contador = 0;
      cambiar_envio(numero_signo_vital);
      Serial.println("");
      Serial.println("");
      Serial.println("---------------------------------");
      Serial.println("");
      Serial.println("");
      if (numero_signo_vital == 3)
      {
        bandera_esperar_enviar_datos = 1;
      }
    }
    else
    {
      Serial.println("Error de confirmacion");
      contador = 0;
      cambiar_envio(numero_signo_vital);
      Serial.println("");
      Serial.println("");
      Serial.println("---------------------------------");
      Serial.println("");
      Serial.println("");
      if (numero_signo_vital == 3)
      {
        bandera_esperar_enviar_datos = 1;
      }
    }

  }
  if (contador == 14000)
  {
    Serial.println("No llego la confirmacion");
    contador = 0;
    cambiar_envio(numero_signo_vital);
    Serial.println("");
    Serial.println("");
    Serial.println("---------------------------------");
    Serial.println("");
    Serial.println("");
    if (numero_signo_vital == 3)
    {
      bandera_esperar_enviar_datos = 1;
    }
  }
}
void envia_signos_vitales()
{

  if (bandera_esperar_enviar_datos == 0)
  {
    if (orden_de_envio == 0)
    {
      envio_signo_vital(temperatura, orden_de_envio);
    }
    if (orden_de_envio == 1)
    {
      envio_signo_vital(frecuencia_respiratoria, orden_de_envio);
    }
    if (orden_de_envio == 2)
    {
      envio_signo_vital(presion_arterial, orden_de_envio);
    }
    if (orden_de_envio == 3)
    {
      envio_signo_vital(frecuencia_cardiaca, orden_de_envio);
    }
  }
  else
  {
    contador_leer_firebase_para_enviar++;
    if (contador_leer_firebase_para_enviar == 5000)
    {
      contador_leer_firebase_para_enviar = 0;
      bandera_esperar_enviar_datos = 0;
      bandera_leer_firebase = 0;
      orden_de_envio = 0;
    }
  }

  contador++;
}
String getValue(String data, String key)
{
  int index = data.indexOf(key);
  if (index != -1)
  {
    int startIndex = data.indexOf(":", index) + 2;    // El valor comienza después de ":"
    int endIndex = data.indexOf('"', startIndex + 1); // El valor termina en la siguiente comilla
    return data.substring(startIndex, endIndex);
  }
  else
  {
    return "Valor no encontrado";
  }
}
void conseguir_datos_firebae()
{
  Firebase.begin(FIREBASE_HOST, FIREBASE_AUTH);
  // Intenta obtener los datos de Firebase
  if (Firebase.getString(firebaseData, DATABASE_PATH))
  {
    // Verifica si los datos recibidos son de tipo string
    if (firebaseData.dataType() == "json")
    {
      // Extrae los datos recibidos y los imprime en el monitor serie
      String jsonData = firebaseData.jsonString();
      Serial.println("Datos JSON recibidos de Firebase: " + jsonData);

      // Parsea los datos JSON
      StaticJsonDocument<256> doc;
      DeserializationError error = deserializeJson(doc, jsonData);

      // Verifica si hubo un error al parsear los datos JSON
      if (error)
      {
        Serial.print("Error al parsear datos JSON: ");
        Serial.println(error.c_str());
      }
      else
      {
        // Lee los valores individuales del documento JSON

        String presionArterial = doc["Presion_arterial"];
        String ritmoCardiaco = doc["Ritmo_cardiaco"];
        String Temperatura = doc["Temperatura"];
        String ritmoRespiratorio = doc["ritmo_respiratorio"];

        frecuencia_respiratoria = ritmoRespiratorio;
        temperatura = Temperatura;
        presion_arterial = presionArterial;
        frecuencia_cardiaca = ritmoCardiaco;

        // Imprime los datos en el monitor serie
        Serial.println("Presion arterial: " + presionArterial);
        Serial.println("Ritmo cardiaco: " + ritmoCardiaco);
        Serial.println("Temperatura: " + temperatura);
        Serial.println("Ritmo respiratorio: " + frecuencia_respiratoria);
      }
    }
    else
    {
      Serial.println("Error: Los datos recibidos no son de tipo JSON");
    }
  }
  else
  {
    // Si hay un error al obtener los datos de Firebase, imprime el motivo del error
    Serial.println("Error al obtener datos de Firebase: " + firebaseData.errorReason());
  }
  firebaseData.clear();
}
void setupPines()
{
  pinMode(LED_wifi, OUTPUT);
  digitalWrite(LED_wifi, LOW);

  pinMode(pin_pulsador, INPUT_PULLUP);
}
void setup()
{
  Serial.begin(115200);
  Serial.println();
  // Conectarse a la red WiFi
  setupPines();
  setupWiFi();
}
void loop()
{
  estado_pulsador = digitalRead(pin_pulsador);
  if (WiFi.status() != WL_CONNECTED)
  {
    titileo_led_wifi();

    contador_reinicio++;
    if (contador_reinicio == 10000)
    {
      contador_reinicio = 0;
      resetSoftware(); // Reinicia el programa
    }
  }
  else
  {
    digitalWrite(LED_wifi, HIGH); // Activa el LED WiFi
    contador_reinicio = 0;        // Reinicia el contador de reinicio
    if ((estado_pulsador == LOW) && (bandera_pulsador == 0))
    {
      bandera_pulsador = 1;
      activar_sistema = 1;
    }
    if ((estado_pulsador == HIGH) && (bandera_pulsador == 1))
    {
      bandera_pulsador = 0;
      activar_sistema = 0;

      Serial.println("se apaga el sistema");
    }
    if (activar_sistema == 1)
    {
      if (bandera_leer_firebase == 0)
      {
        bandera_leer_firebase = 1;
        orden_de_envio = 0;
        contador = 0;
        Serial.println("lee en firebase");
        conseguir_datos_firebae();
      }
      envia_signos_vitales();
    }
    else
    {
      orden_de_envio = 0;
      bandera_esperar_enviar_datos = 0;
      contador = 0;
    }
  }
  delay(1);
}
