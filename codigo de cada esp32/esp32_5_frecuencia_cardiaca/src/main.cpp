#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <LiquidCrystal_I2C.h>

const char *ssid = "simulador_pacientes";
const char *password = "simulador9507";
// const char *ssid = "redmicote";
// const char *password = "cotemaster";
const int udpPort = 12345;   // Puerto UDP arbitrario

int bandera_mensaje=0;
int contador_mensaje=0;
int lcdColumns = 16;
int lcdRows = 2;
IPAddress remoteIP;
String control_frecuencia_cardiaca= "";
int remotePort;
LiquidCrystal_I2C lcd(0x27, lcdColumns, lcdRows); 
WiFiUDP udp;

String datoExtraido = "";
void mostrar_lcd(int mostrar,String dato){
  switch (mostrar)
  {
  case 0:
    lcd.setCursor(0, 0);
    lcd.print("frecuencia C.:");

    lcd.setCursor(0, 1);
    lcd.print("sin valor");
    break;
  case 1:
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("se envia");

    lcd.setCursor(0, 1);
    lcd.print(dato);
    lcd.print("res.. f.c");
    break;
  case 2:
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("C. frecuencia C.:");
    lcd.setCursor(0, 1);
    lcd.print(dato);
    lcd.print(" rpm");
    break;
  case 3:
    lcd.setCursor(0, 0);
    lcd.print("Frecuencia C.:");
    lcd.setCursor(0, 1);
    lcd.print(dato);
    lcd.print(" rpm");
    break;
  default:
    break;
  }
}
String extraerDato(char *datoCompleto)
{
  // Convierte el array de caracteres a un String
  String datoString = String(datoCompleto);

  // Encontrar la posición del primer '<'
  int inicio = datoString.indexOf('<');

  // Encontrar la posición del primer '>'
  int fin = datoString.indexOf('>', inicio);

  // Extraer la parte entre < y >
  if (inicio != -1 && fin != -1)
  {
    datoString = datoString.substring(inicio + 1, fin);
    // Verificar si la cadena comienza con "temperatura:"
    if (datoString.startsWith("frecuencia_cardiaca:"))
    {
      // Encontrar la posición del primer ':'
      int inicioNumero = datoString.indexOf(':');

      // Extraer la parte después del ':'
      return datoString.substring(inicioNumero + 1);
    }
    else
    {
      return "No se encontró la palabra clave 'frecuencia_cardiaca:'";
    }
  }
  else
  {
    return "No se encontraron los caracteres '<>'";
  }
}
void setup()
{
  Serial.begin(115200);
  Serial.println();

  lcd.init();
  lcd.backlight();
  randomSeed(analogRead(A0));  // Inicializa la semilla del generador de números aleatorios
    // Ajusta el contraste aquí, puedes probar diferentes valores entre 0 y 255
  //lcd.command(0x21); // Comando para ajustar el modo de función LCD extendido
  ///lcd.command(0x80 | 100); // Ajusta el contraste, el valor "50" es solo un ejemplo, ajusta según sea necesario
  //lcd.command(0x20); // Vuelve al modo de función básico
  // Conectarse a la red WiFi
  // Conectarse a la red WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(1000);
    Serial.println("Conectando a WiFi...");
  }
  Serial.println("Conectado a WiFi");

  // Asignar la dirección IP fija al ESP32 servidor
  IPAddress localIP(192, 168, 1, 104); // Cambia esto según tu configuración
  IPAddress gateway(192, 168, 1, 1);   // Cambia esto según tu configuración
  IPAddress subnet(255, 255, 255, 0);  // Cambia esto según tu configuración
  WiFi.config(localIP, gateway, subnet);

  // Comenzar el servicio UDP
  udp.begin(udpPort);
  Serial.printf("Servidor UDP iniciado en la dirección IP %s, puerto %d\n", localIP.toString().c_str(), udpPort);
}

void loop()
{
  // Escuchar por paquetes UDP entrantes
  int packetSize = udp.parsePacket();
  if (packetSize)
  {
    lcd.clear();
    bandera_mensaje = 1;
    remoteIP = udp.remoteIP();
    remotePort = udp.remotePort();
    Serial.printf("Recibido %d bytes desde %s, puerto %d\n", packetSize, remoteIP.toString().c_str(), remotePort);
    char incomingPacket[255];
    udp.read(incomingPacket, sizeof(incomingPacket));
    datoExtraido = extraerDato(incomingPacket);
    Serial.println("Control de frecuencia cardiaca: " + datoExtraido);
    mostrar_lcd(2,datoExtraido);
    control_frecuencia_cardiaca = datoExtraido;
    Serial.print("bandera mensaje:");
    Serial.println(bandera_mensaje);
  }
if(bandera_mensaje == 1){
  contador_mensaje++;
  if(contador_mensaje == 4000){
  lcd.clear();
  mostrar_lcd(bandera_mensaje,datoExtraido);
  udp.beginPacket(remoteIP, remotePort);
  udp.print(">respuesta_temperatura:"+control_frecuencia_cardiaca+"<");
  udp.endPacket();
  mostrar_lcd(bandera_mensaje,datoExtraido);
  }
  if(contador_mensaje == 8000){
  lcd.clear();
  bandera_mensaje = 2;
  
  contador_mensaje=0;

  }
}
if(bandera_mensaje == 2){
  mostrar_lcd(3,control_frecuencia_cardiaca);

}

if(bandera_mensaje == 0){
  mostrar_lcd(0,datoExtraido);
}
delay(1);
}
