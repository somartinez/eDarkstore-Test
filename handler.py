import json
import requests
import boto3
import datetime
from fpdf import FPDF
from decimal import Decimal

# Class obtenida de ejemplo de https://mindicador.cl por Isabel Vega Villablanca.

class Mindicador:
    def __init__(self, indicador):
        self.indicador = indicador
    
    def info_api(self):
        url = f'https://mindicador.cl/api/{self.indicador}'
        response = requests.get(url)
        if response.status_code != 200:
            return None  
        return response.json()
    

# Funcion referenciada de https://www.geeksforgeeks.org/creating-pdf-documents-with-python/

def create_pdf(value, date):

    pdf_file_name = f"/tmp/uf_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    pdf = FPDF()

    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f'Valor UF: {value} para la fecha: {date}', ln=True, align='C')
    pdf.output(pdf_file_name)

    return pdf_file_name

def get_uf(event, context):

# Se obtiene la data de Uf
    
    indicador_uf = Mindicador('uf')
    uf_data = indicador_uf.info_api()
    
    # 'serie' almacena en la posicion 0 la informacion del día actual (Last in First out)

    uf_value = uf_data['serie'][0]['valor']
    uf_date = uf_data['serie'][0]['fecha']

    # Se modifica la fecha para simplicar

    formatted_uf_date = datetime.datetime.strptime(uf_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d-%m-%Y %H:%M")

    pdf_filename = create_pdf(uf_value, formatted_uf_date)

    # https://www.geeksforgeeks.org/how-to-upload-and-download-files-from-aws-s3-using-python/

    s3 = boto3.client('s3')

    bucket_name = "serverless-framework-deployments-us-east-1-8812123d-e2d7"

    s3.upload_file(
        pdf_filename, 
        bucket_name, 
        pdf_filename)

    return {
        "statusCode": 200,
        "body": f"La UF posee un valor de: {uf_value} para la fecha: {formatted_uf_date} y se ha guardado en el PDF: {pdf_filename}"
    }

def get_dollar(event, context):

    # Se obtiene tabla creada en AWS

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('eDarkstore-Dollar')

    # Se obtiene datos del dolar para el día actual  

    indicador_dolar = Mindicador('dolar')
    dolar_data = indicador_dolar.info_api()

    # 'serie' almacena en la posicion 0 la informacion del día actual (Last in First out)

    dolar_value = int(dolar_data['serie'][0]['valor'])

    dolar_date = dolar_data['serie'][0]['fecha']

    formatted_dolar_date = datetime.datetime.strptime(dolar_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d-%m-%Y %H:%M")

    # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/programming-with-python.html

    table.put_item(
        Item = {
            'date': formatted_dolar_date,
            'value': Decimal(dolar_value)
        }
    )

    return {
        "statusCode": 200,
        "body": f"Dolar value: {dolar_value}, para el dia {formatted_dolar_date}"
    }
