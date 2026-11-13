import os
import numpy as np
import pandas as pd
from django.conf import settings
from timesfm3 import TimesFM3Evaluator, ModelConfig
from .models import EstadoFinanciero


def predecir_metrica_financiera_torch(
    usuario_id=None,
    metrica: str = "utilidad_neta",
    horizonte_meses: int = 6,
):
  # 1. Obtener el histórico desde el ORM
  qs = EstadoFinanciero.objects.all()
  if usuario_id:
    qs = qs.filter(usuario_id=usuario_id)

  qs = qs.order_by("fecha_fin")

  registros = []
  for obj in qs:
    valor_obj = getattr(obj, metrica)
    if hasattr(valor_obj, "amount"):
      val = float(valor_obj.amount)
    elif valor_obj is not None:
      val = float(valor_obj)
    else:
      val = 0.0

    registros.append({"fecha": obj.fecha_fin, "valor": val})

  df = pd.DataFrame(registros)
  if df.empty or len(df) < 3:
    raise ValueError(
        "No hay suficientes datos históricos para generar un pronóstico."
    )

  # 2. Normalizar y asegurar periodicidad mensual
  df["fecha"] = pd.to_datetime(df["fecha"])
  df = df.set_index("fecha").resample("ME").last().fillna(0.0)

  context_data = df["valor"].astype(np.float32).values

  # 3. Ruta exacta del checkpoint local o nombre del modelo de Hugging Face
  checkpoint_path = os.path.join(
      settings.BASE_DIR, 
      "models", 
      "timesfm", 
      "checkpoints", 
      "checkpoints", 
      "checkpoint_1100000"
  )
  
  # Si prefieres usar la ruta local que armaste, asegúrate de que exista, 
  # o usa directamente el identificador si descargas online: "google/timesfm-3.0-pytorch"
  path_a_usar = checkpoint_path if os.path.exists(checkpoint_path) else "google/timesfm-3.0-pytorch"

  # CORRECCIÓN: Inicialización oficial para TimesFM 3.0
  config = ModelConfig(
      checkpoint_path=path_a_usar,
      per_core_batch_size=32,
      device="cpu"  # Cambiar a "cpu" si tu entorno de Docker no cuenta con GPU disponible
  )
  forecaster = TimesFM3Evaluator(config)

  # 4. Ejecutar inferencia por lotes (retorna una lista de resultados)
  outputs = list(
      forecaster.predict_batch(
          [context_data], 
          horizon=horizonte_meses, 
          return_quantiles=True, 
          use_symmetric_averaging=False
      )
  )

  resultado = outputs[0]

  return {
      "historico": df["valor"].tolist(),
      "fechas_historico": df.index.strftime("%Y-%m-%d").tolist(),
      "pronostico_punto": resultado.forecast.tolist(),
      "cuantiles": (
          resultado.quantiles.tolist()
          if hasattr(resultado, "quantiles") and resultado.quantiles is not None
          else None
      ),
  }


  #Esto va en models.py--------------------------------------------------------

      # ==============================
    # MÉTODO DE PREDICCIÓN INDIVIDUAL
    # ==============================
    def ejecutar_y_guardar_prediccion_individual(self, metrica='utilidad_neta', meses=6):
        if not self.usuario:
            return {"error": "Este estado financiero no tiene un usuario asociado."}
        
        from .services import predecir_metrica_financiera_torch
        
        try:
            resultado = predecir_metrica_financiera_torch(
                usuario_id=self.usuario.id,
                metrica=metrica,
                horizonte_meses=meses
            )
            
            puntos = resultado.get("pronostico_punto", [])
            campos_meses = ['pred_mes_1', 'pred_mes_2', 'pred_mes_3', 'pred_mes_4', 'pred_mes_5', 'pred_mes_6']
            campos_actualizados = ['fecha_ultima_prediccion']
            
            for i, campo_nombre in enumerate(campos_meses):
                if i < len(puntos):
                    val = round(float(puntos[i]), 2)
                    setattr(self, campo_nombre, Money(val, 'USD'))
                else:
                    setattr(self, campo_nombre, None)
                
                campos_actualizados.append(campo_nombre)
            
            self.fecha_ultima_prediccion = timezone.now()
            self.save(update_fields=campos_actualizados)
            
            return {"success": True, "valores_guardados": puntos}
            
        except Exception as e:
            return {"error": str(e)}