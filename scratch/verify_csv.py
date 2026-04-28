import sys
import os
from unittest.mock import MagicMock

# Mocking necessary Flask and SQLAlchemy components
sys.modules['flask_sqlalchemy'] = MagicMock()
sys.modules['flask_login'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['werkzeug.security'] = MagicMock()

# Add project root to path
sys.path.append(os.getcwd())

import io
import csv

# Mock models
class MockUser:
    def __init__(self, nombre, apellido, email, rol, carreras=None, carrera_id=None):
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.rol = rol
        self.carreras = carreras or []
        self.carrera_id = carrera_id
        self.telefono = "123456789"

class MockCarrera:
    def __init__(self, codigo):
        self.codigo = codigo

# Re-implementing the function here for verification since we can't easily import from utils without full env
def test_exportar_profesores_csv(profesores):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['nombre', 'apellido_paterno', 'apellido_materno', 'email', 'telefono', 'rol', 'tipo_profesor', 'carrera_codigo'])
    
    for p in profesores:
        apellidos = p.apellido.split(' ', 1)
        paterno = apellidos[0] if len(apellidos) > 0 else p.apellido
        materno = apellidos[1] if len(apellidos) > 1 else ''
        
        rol = 'profesor' if p.rol in ['profesor_completo', 'profesor_asignatura'] else p.rol
        tipo = p.rol if p.rol in ['profesor_completo', 'profesor_asignatura'] else ''
        
        carreras = ""
        if p.rol == 'jefe_carrera' and p.carrera_id:
            # In actual code it queries Carrera.query.get(p.carrera_id)
            carreras = "J_CARRERA" # Mocked
        elif p.carreras:
            carreras = ','.join([c.codigo for c in p.carreras])
            
        writer.writerow([p.nombre, paterno, materno, p.email, p.telefono or '', rol, tipo, carreras])
    
    return output.getvalue()

# Test data
c1 = MockCarrera("ISC")
c2 = MockCarrera("IRO")

p1 = MockUser("Juan", "Perez Garcia", "juan@test.com", "profesor_completo", [c1, c2])
p2 = MockUser("Maria", "Lopez", "maria@test.com", "jefe_carrera", carrera_id=1)

csv_out = test_exportar_profesores_csv([p1, p2])
print("Generated CSV:")
print(csv_out)

# Verify parsing
import pandas as pd
df = pd.read_csv(io.StringIO(csv_out))
print("\nParsed DataFrame:")
print(df)

if "ISC,IRO" in df.iloc[0]['carrera_codigo']:
    print("\nSUCCESS: Multiple careers correctly quoted and parsed as a single field.")
else:
    print("\nFAILURE: Multiple careers not correctly handled.")
