from flask import Flask, render_template, request, jsonify
from flask_wtf import CSRFProtect
from database import get_connection
from datetime import datetime
from decimal import Decimal

app = Flask(__name__)
csrf = CSRFProtect()
csrf.init_app(app)

SMMLV = 1300000  # Actualiza el salario mínimo cada año

# Constantes para las tasas de horas extras
TASA_HORA_DIURNA = Decimal(1.25)
TASA_HORA_NOCTURNA = Decimal(1.75)
TASA_HORA_FESTIVA_DIA = Decimal(2)
TASA_HORA_FESTIVA_NOCHE = Decimal(2.5)
TASA_HORA_DOMINICAL = Decimal(1.75)

def calcular_horas_extras(horas_diurnas, horas_nocturnas, horas_festivas_dia, horas_festivas_noche, horas_dominicales, costo):
    return (
        (horas_diurnas * costo * TASA_HORA_DIURNA) +
        (horas_nocturnas * costo * TASA_HORA_NOCTURNA) +
        (horas_festivas_dia * costo * TASA_HORA_FESTIVA_DIA) +
        (horas_festivas_noche * costo * TASA_HORA_FESTIVA_NOCHE) +
        (horas_dominicales * costo * TASA_HORA_DOMINICAL)
    )

def calcular_incapacidad(salario_base, tipo_incapacidad, dias_incapacidad):
    valor_incapacidad = 0
    if tipo_incapacidad != 'ninguna' and dias_incapacidad > 0:
        if tipo_incapacidad == 'comun':
            if dias_incapacidad <= 2:
                valor_incapacidad = salario_base / 30 * dias_incapacidad
            else:
                valor_incapacidad = ((salario_base / 30) * 2) + ((salario_base / 30 * 0.6667) * (dias_incapacidad - 2))
        else:
            valor_incapacidad = (salario_base / 30) * dias_incapacidad
    return valor_incapacidad

def calcular_vacaciones(salario_base, fecha_ingreso, fecha_corte):
    valor_vacaciones = 0
    if fecha_ingreso and fecha_corte:
        try:
            fecha_ingreso_dt = datetime.strptime(fecha_ingreso, "%Y-%m-%d")
            fecha_corte_dt = datetime.strptime(fecha_corte, "%Y-%m-%d")
            dias_trabajados = (fecha_corte_dt - fecha_ingreso_dt).days
            dias_vacaciones = (15 / 360) * dias_trabajados
            valor_vacaciones = (salario_base / 30) * dias_vacaciones
        except ValueError:
            valor_vacaciones = 0
    return valor_vacaciones

def calcular_deducciones(salario_base):
    salud = salario_base * Decimal(0.04)
    pension = salario_base * Decimal(0.04)
    fondo_solidaridad = salario_base * Decimal(0.01) if salario_base > (4 * SMMLV) else 0
    return salud, pension, fondo_solidaridad

@app.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM colegios")
    colegios = cursor.fetchall()
    conn.close()
    return render_template('form.html', colegios=colegios)

@app.route('/prendas/<int:colegio_id>')
def obtener_prendas(colegio_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM prendas WHERE colegio_id = %s", (colegio_id,))
    prendas = cursor.fetchall()
    conn.close()
    return jsonify(prendas)

@app.route('/operaciones/<int:prenda_id>')
def obtener_operaciones(prenda_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, costo FROM operaciones WHERE prenda_id = %s", (prenda_id,))
    operaciones = cursor.fetchall()
    conn.close()
    return jsonify(operaciones)

@app.route('/guardar', methods=['POST'])
def guardar():
    # Datos básicos del formulario
    fecha = request.form['fecha']
    hora = request.form['hora']
    colegio_id = request.form['colegio']
    prenda_id = request.form['prenda']
    operacion_id = request.form['operacion']
    cantidad = int(request.form['cantidad'])
    operario = request.form['operario']

    # Datos nuevos del formulario
    horas_diurnas = Decimal(request.form.get('horas_diurnas', 0))
    horas_nocturnas = Decimal(request.form.get('horas_nocturnas', 0))
    horas_festivas_dia = Decimal(request.form.get('horas_festivas_dia', 0))
    horas_festivas_noche = Decimal(request.form.get('horas_festivas_noche', 0))
    horas_dominicales = Decimal(request.form.get('horas_dominicales', 0))

    tipo_incapacidad = request.form.get('tipo_incapacidad', 'ninguna')
    dias_incapacidad = Decimal(request.form.get('dias_incapacidad', 0))

    fecha_ingreso = request.form.get('fecha_ingreso')
    fecha_corte = request.form.get('fecha_corte')

    fecha_ingreso = fecha_ingreso if fecha_ingreso else None
    fecha_corte = fecha_corte if fecha_corte else None

    # Conexión a la base de datos
    conn = get_connection()
    cursor = conn.cursor()

    # Obtener el costo de la operación
    cursor.execute("SELECT costo FROM operaciones WHERE id = %s", (operacion_id,))
    costo = cursor.fetchone()[0]

    # 1. Calcular valor por operaciones normales
    valor_total_operaciones = cantidad * costo

    # 2. Calcular horas extras
    valor_horas_extras = calcular_horas_extras(horas_diurnas, horas_nocturnas, horas_festivas_dia, horas_festivas_noche, horas_dominicales, costo)

    # 3. Salario base
    salario_base = valor_total_operaciones + valor_horas_extras

    # 4. Calcular incapacidades
    valor_incapacidad = calcular_incapacidad(salario_base, tipo_incapacidad, dias_incapacidad)

    # 5. Calcular vacaciones
    valor_vacaciones = calcular_vacaciones(salario_base, fecha_ingreso, fecha_corte)

    # 6. Deducciones
    salud, pension, fondo_solidaridad = calcular_deducciones(salario_base)
    total_deducciones = salud + pension + fondo_solidaridad

    # 7. Salario Neto
    salario_neto = (salario_base + valor_incapacidad + valor_vacaciones) - total_deducciones

    # Insertar en la base de datos
    cursor.execute('''
        INSERT INTO registro 
        (fecha, hora, colegio_id, prenda_id, operacion_id, cantidad, total, operario,
         horas_diurnas, horas_nocturnas, horas_festivas_dia, horas_festivas_noche, horas_dominicales,
         tipo_incapacidad, dias_incapacidad, fecha_ingreso, fecha_corte,
         valor_incapacidad, valor_vacaciones, salud, pension, fondo_solidaridad, salario_neto)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        fecha, hora, colegio_id, prenda_id, operacion_id, cantidad, valor_total_operaciones, operario,
        horas_diurnas, horas_nocturnas, horas_festivas_dia, horas_festivas_noche, horas_dominicales,
        tipo_incapacidad, dias_incapacidad, fecha_ingreso, fecha_corte,
        valor_incapacidad, valor_vacaciones, salud, pension, fondo_solidaridad, salario_neto
    ))
    conn.commit()
    conn.close()

    return render_template("success.html",
                           operario=operario,
                           total=valor_total_operaciones,
                           valor_extras=valor_horas_extras,
                           valor_incapacidad=valor_incapacidad,
                           valor_vacaciones=valor_vacaciones,
                           fecha=datetime.now().strftime('%Y-%m-%d'))

if __name__ == "__main__":
    app.run(debug=False)
