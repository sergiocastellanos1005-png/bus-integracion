from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Bus de integración")

# ---- Datos de ejemplo ----
inventario = {"arroz": 50, "carne de res": 15, "aceite": 12}
facturas = []
log = []

# ---- Servicios (cada uno recibe un payload y devuelve un resultado) ----
def servicio_inventario(payload: dict) -> dict:
    if "producto" not in payload:
        raise ValueError("Falta el campo 'producto'")
    producto = payload["producto"]
    if producto not in inventario:
        return {"producto": producto, "existe": False}
    return {"producto": producto, "existe": True, "stock": inventario[producto]}

def servicio_facturacion(payload: dict) -> dict:
    for campo in ("cliente", "producto", "cantidad", "precio"):
        if campo not in payload:
            raise ValueError(f"Falta el campo '{campo}'")
    factura = {
        "id": len(facturas) + 1,
        "cliente": payload["cliente"],
        "producto": payload["producto"],
        "total": payload["cantidad"] * payload["precio"],
        "fecha": datetime.now().isoformat(timespec="seconds"),
    }
    facturas.append(factura)
    return factura

# ---- Registro: tipo de mensaje -> servicio ----
REGISTRO = {
    "inventario": servicio_inventario,
    "facturacion": servicio_facturacion,
}

# ---- Modelo del mensaje que entra al bus ----
class Mensaje(BaseModel):
    tipo: str
    payload: dict = Field(default_factory=dict)

# ---- Endpoints ----
@app.get("/")
def inicio():
    return {"mensaje": "Bus de integración activo", "servicios": list(REGISTRO)}

@app.post("/mensajes")
def enrutar(msg: Mensaje):
    servicio = REGISTRO.get(msg.tipo)
    if servicio is None:
        raise HTTPException(status_code=404, detail=f"Servicio '{msg.tipo}' no registrado")
    try:
        resultado = servicio(msg.payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    log.append({"tipo": msg.tipo, "estado": "ok", "hora": datetime.now().isoformat(timespec="seconds")})
    return {"estado": "ok", "resultado": resultado}

@app.get("/log")
def ver_log():
    return log
