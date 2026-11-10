from abc import ABC, abstractmethod

from models import Estudiante, Materia, Matricula
from shared.json_manager import GestorJSON
from shared.herramientas import es_email_valido


# =====================================================================
# CLASE BASE (ABSTRACTA)
# =====================================================================
# Solo dice QUÉ métodos debe tener todo controlador.
# CÓMO se hace cada uno lo escribe cada controlador, de la forma más simple.
class CrudBase(ABC):
    @abstractmethod
    def leer(self):
        pass

    @abstractmethod
    def obtener(self, id_registro):
        pass

    @abstractmethod
    def buscar(self, texto):
        pass

    @abstractmethod
    def siguiente(self):
        pass

    @abstractmethod
    def crear(self, datos):
        pass

    @abstractmethod
    def actualizar(self, id_registro, datos):
        pass

    @abstractmethod
    def eliminar(self, id_registro):
        pass


# =====================================================================
# CONTROLADOR DE ESTUDIANTES
# =====================================================================
class EstudianteController(CrudBase):
    # TUPLA: campos obligatorios y campos buscables. Son fijos, por eso no son listas.
    OBLIGATORIOS = ("nombre", "apellido", "email", "carnet")
    CAMPOS_BUSCABLES = ("nombre", "apellido", "email", "carnet", "carrera")

    def __init__(self, archivo="data/estudiantes.json"):
        self.gestor = GestorJSON(archivo)
        # LISTA: guarda los objetos en orden de llegada y permite recorrerlos
        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Estudiante.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for estudiante in self.lista:
            datos.append(estudiante.a_diccionario())
        self.gestor.guardar(datos)

    def carnets_registrados(self, excepto_id=None):
        # CONJUNTO: carnets ya usados. Preguntar 'x in conjunto' es instantáneo
        # y además elimina repetidos sin esfuerzo.
        return {e.carnet.upper() for e in self.lista if e.id != excepto_id}

    def emails_registrados(self, excepto_id=None):
        # CONJUNTO: mismo motivo que los carnets, para detectar emails repetidos.
        return {e.email.lower() for e in self.lista if e.id != excepto_id}

    def validar(self, datos, id_actual=None):
        """Devuelve un mensaje de error, o None si todo está bien."""
        # 1) obligatorios (solo al crear; al actualizar basta con lo que cambia)
        if id_actual is None:
            for campo in self.OBLIGATORIOS:
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"
        else:
            for campo in self.OBLIGATORIOS:
                if campo in datos and str(datos[campo]).strip() == "":
                    return f"El campo {campo} no puede quedar vacío"
        # 2) email válido y único
        if "email" in datos:
            email = str(datos["email"]).strip().lower()
            if not es_email_valido(email):
                return f"Email inválido: '{email}'"
            if email in self.emails_registrados(id_actual):
                return "Ese email ya está registrado"
        # 3) carnet no repetido
        if "carnet" in datos:
            carnet = str(datos["carnet"]).strip().upper()
            if carnet in self.carnets_registrados(id_actual):
                return f"El carnet {carnet} ya está registrado"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_estudiante):
        for estudiante in self.lista:
            if estudiante.id == id_estudiante:
                return estudiante
        return None

    def buscar(self, texto):
        texto = texto.strip().lower()
        encontrados = []
        if texto == "":
            return encontrados
        for estudiante in self.lista:
            for campo in self.CAMPOS_BUSCABLES:
                if texto in str(getattr(estudiante, campo)).lower():
                    encontrados.append(estudiante)
                    break                       # ya coincidió: no repetirlo
        return encontrados

    def siguiente(self):
        mayor = 0
        for estudiante in self.lista:
            if estudiante.id > mayor:
                mayor = estudiante.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error
        estudiante = Estudiante(self.siguiente(),
                                str(datos["nombre"]).strip().title(),
                                str(datos["apellido"]).strip().title(),
                                str(datos["email"]).strip().lower(),
                                str(datos["carnet"]).strip().upper(),
                                str(datos.get("carrera", "")).strip().title())
        self.lista.append(estudiante)
        self.guardar()
        return True, f"Estudiante creado: {estudiante.etiqueta()}"

    def actualizar(self, id_estudiante, datos):
        estudiante = self.obtener(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"
        if not datos:
            return False, "No se indicó ningún cambio"
        # DIFERENCIA de conjuntos: campos que no existen en un estudiante
        permitidos = {"nombre", "apellido", "email", "carnet", "carrera"}
        desconocidos = set(datos) - permitidos
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"
        # Se valida ANTES de tocar el objeto: si algo falla, no cambia nada
        error = self.validar(datos, id_estudiante)
        if error:
            return False, error
        for campo, valor in datos.items():
            valor = str(valor).strip()
            if campo in ("nombre", "apellido", "carrera"):
                valor = valor.title()
            elif campo == "email":
                valor = valor.lower()
            elif campo == "carnet":
                valor = valor.upper()
            setattr(estudiante, campo, valor)
        self.guardar()
        return True, f"Estudiante {id_estudiante} actualizado"

    def eliminar(self, id_estudiante):
        estudiante = self.obtener(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"
        self.lista.remove(estudiante)
        self.guardar()
        return True, f"Estudiante {id_estudiante} eliminado"

    # --- propio de estudiantes ---
    def carreras(self):
        """CONJUNTO de carreras: sin repetidas. sorted() lo devuelve como lista."""
        return sorted({e.carrera for e in self.lista if e.carrera != ""})

    # Nombres alineados con la tarea (16.4): delegan en los métodos CRUD
    def crear_estudiante(self, datos):
        return self.crear(datos)

    def obtener_estudiantes(self):
        return self.leer()

    def obtener_estudiante(self, id_estudiante):
        return self.obtener(id_estudiante)

    def buscar_estudiantes(self, termino):
        return self.buscar(termino)

    def actualizar_estudiante(self, id_estudiante, cambios):
        return self.actualizar(id_estudiante, cambios)

    def eliminar_estudiante(self, id_estudiante):
        return self.eliminar(id_estudiante)


# =====================================================================
# CONTROLADOR DE MATERIAS
# =====================================================================
class MateriaController(CrudBase):
    OBLIGATORIOS = ("nombre", "codigo", "creditos")          # TUPLA: fija
    CAMPOS_BUSCABLES = ("nombre", "codigo")                  # TUPLA: fija

    def __init__(self, archivo="data/materias.json"):
        self.gestor = GestorJSON(archivo)
        self.lista = []                                       # LISTA de objetos Materia
        for datos in self.gestor.leer():
            self.lista.append(Materia.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for materia in self.lista:
            datos.append(materia.a_diccionario())
        self.gestor.guardar(datos)

    def codigos_registrados(self, excepto_id=None):
        # CONJUNTO: códigos ya usados; 'in' es instantáneo y no admite repetidos
        return {m.codigo.upper() for m in self.lista if m.id != excepto_id}

    def validar(self, datos, id_actual=None):
        if id_actual is None:
            for campo in self.OBLIGATORIOS:
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"
        else:
            for campo in ("nombre", "codigo"):
                if campo in datos and str(datos[campo]).strip() == "":
                    return f"El campo {campo} no puede quedar vacío"
        if "codigo" in datos:
            codigo = str(datos["codigo"]).strip().upper()
            if codigo in self.codigos_registrados(id_actual):
                return f"El código {codigo} ya está registrado"
        if "creditos" in datos:
            creditos = str(datos["creditos"]).strip()
            if not creditos.isdigit() or not 1 <= int(creditos) <= 10:
                return "Los créditos deben ser un entero entre 1 y 10"
        if "cupos" in datos and str(datos["cupos"]).strip() != "":
            cupos = str(datos["cupos"]).strip()
            if not cupos.isdigit() or not 0 <= int(cupos) <= Materia.CUPOS_MAXIMOS:
                return f"Los cupos deben ser un entero entre 0 y {Materia.CUPOS_MAXIMOS}"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_materia):
        for materia in self.lista:
            if materia.id == id_materia:
                return materia
        return None

    def buscar(self, texto):
        texto = texto.strip().lower()
        encontradas = []
        if texto == "":
            return encontradas
        for materia in self.lista:
            for campo in self.CAMPOS_BUSCABLES:
                if texto in str(getattr(materia, campo)).lower():
                    encontradas.append(materia)
                    break
        return encontradas

    def siguiente(self):
        mayor = 0
        for materia in self.lista:
            if materia.id > mayor:
                mayor = materia.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error
        # Si no escribieron los cupos, la materia abre con el máximo
        cupos = str(datos.get("cupos", "")).strip()
        materia = Materia(self.siguiente(),
                          str(datos["nombre"]).strip().title(),
                          str(datos["codigo"]).strip().upper(),
                          int(str(datos["creditos"]).strip()),
                          int(cupos) if cupos != "" else Materia.CUPOS_MAXIMOS)
        self.lista.append(materia)
        self.guardar()
        return True, f"Materia creada: {materia.etiqueta()}"

    def actualizar(self, id_materia, datos):
        materia = self.obtener(id_materia)
        if materia is None:
            return False, f"No existe una materia con id {id_materia}"
        if not datos:
            return False, "No se indicó ningún cambio"
        desconocidos = set(datos) - {"nombre", "codigo", "creditos", "cupos"}
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"
        error = self.validar(datos, id_materia)
        if error:
            return False, error
        if "nombre" in datos:
            materia.nombre = str(datos["nombre"]).strip().title()
        if "codigo" in datos:
            materia.codigo = str(datos["codigo"]).strip().upper()
        if "creditos" in datos:
            materia.creditos = int(datos["creditos"])
        if "cupos" in datos:
            materia.cupos = int(datos["cupos"])
        self.guardar()
        return True, f"Materia {id_materia} actualizada"

    def eliminar(self, id_materia):
        materia = self.obtener(id_materia)
        if materia is None:
            return False, f"No existe una materia con id {id_materia}"
        self.lista.remove(materia)
        self.guardar()
        return True, f"Materia {id_materia} eliminada"

    # --- propio de materias ---
    def materias_sin_cupo(self):
        sin_cupo = []
        for materia in self.lista:
            if not materia.hay_cupo():
                sin_cupo.append(materia)
        return sin_cupo

    # Nombres alineados con la tarea (16.4)
    def crear_materia(self, datos):
        return self.crear(datos)

    def obtener_materias(self):
        return self.leer()

    def obtener_materia(self, id_materia):
        return self.obtener(id_materia)

    def buscar_materias(self, termino):
        return self.buscar(termino)

    def actualizar_materia(self, id_materia, cambios):
        return self.actualizar(id_materia, cambios)

    def eliminar_materia(self, id_materia):
        return self.eliminar(id_materia)


# =====================================================================
# CONTROLADOR DE MATRÍCULAS
# =====================================================================
class MatriculaController(CrudBase):
    def __init__(self, estudiantes, materias, archivo="data/matriculas.json"):
        # La matrícula USA a los otros dos controladores.
        # Hay que pasarle los MISMOS que usa main.py.
        self.estudiantes = estudiantes
        self.materias = materias
        self.gestor = GestorJSON(archivo)
        self.lista = []                                       # LISTA de objetos Matricula
        for datos in self.gestor.leer():
            self.lista.append(Matricula.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for matricula in self.lista:
            datos.append(matricula.a_diccionario())
        self.gestor.guardar(datos)

    def ids_registrados(self, controlador):
        # CONJUNTO de ids: saber si un id existe es 'x in conjunto', sin recorrer nada
        return {objeto.id for objeto in controlador.leer()}

    def validar(self, datos):
        try:
            estudiante_id = int(datos.get("estudiante_id", 0))
            materia_id = int(datos.get("materia_id", 0))
        except (TypeError, ValueError):
            return "estudiante_id y materia_id deben ser números enteros"
        periodo = str(datos.get("periodo", "")).strip()
        if periodo == "":
            return "El período es obligatorio (ej. 2026-1)"
        # El estudiante debe existir
        if estudiante_id not in self.ids_registrados(self.estudiantes):
            return f"No existe un estudiante con id {estudiante_id}"
        # La materia debe existir y tener cupo
        if materia_id not in self.ids_registrados(self.materias):
            return f"No existe una materia con id {materia_id}"
        materia = self.materias.obtener(materia_id)
        if not materia.hay_cupo():
            return f"La materia {materia.nombre} no tiene cupos disponibles"
        # No matricular dos veces: se comparan LOS TRES datos juntos
        for otra in self.lista:
            if (otra.estudiante_id == estudiante_id
                    and otra.materia_id == materia_id
                    and otra.periodo == periodo):
                return "El estudiante ya está matriculado en esa materia en ese período"
        # La nota, si viene, debe ser de 0 a 20
        nota = str(datos.get("nota", "")).strip()
        if nota != "" and not Materia.es_nota_valida(nota):
            return f"Nota inválida: '{nota}' (debe estar entre 0 y 20)"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_matricula):
        for matricula in self.lista:
            if matricula.id == id_matricula:
                return matricula
        return None

    def buscar(self, texto):
        # Las matrículas se buscan por período, ej: "2026-1"
        texto = texto.strip()
        encontradas = []
        if texto == "":
            return encontradas
        for matricula in self.lista:
            if texto in matricula.periodo:
                encontradas.append(matricula)
        return encontradas

    def siguiente(self):
        mayor = 0
        for matricula in self.lista:
            if matricula.id > mayor:
                mayor = matricula.id
        return mayor + 1

    def crear(self, datos):
        # datos = {"estudiante_id": 1, "materia_id": 2, "periodo": "2026-1"}
        error = self.validar(datos)
        if error:
            return False, error
        materia = self.materias.obtener(int(datos["materia_id"]))
        nota = str(datos.get("nota", "")).strip()
        matricula = Matricula(self.siguiente(),
                              int(datos["estudiante_id"]),
                              materia.id,
                              str(datos["periodo"]).strip(),
                              float(nota) if nota != "" else None)
        materia.ocupar_cupo()
        self.materias.guardar()          # el cupo nuevo vive en materias.json
        self.lista.append(matricula)
        self.guardar()                   # la matrícula vive en matriculas.json
        return True, f"Matrícula {matricula.id} registrada (quedan {materia.cupos} cupos)"

    def actualizar(self, id_matricula, datos):
        # Una matrícula no se edita: la nota se cambia con registrar_nota()
        return False, "Las matrículas no se modifican: use registrar nota o retírela"

    def registrar_nota(self, id_matricula, nota):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return False, f"No existe la matrícula {id_matricula}"
        if not Materia.es_nota_valida(nota):
            return False, f"Nota inválida: '{nota}' (debe estar entre 0 y 20)"
        matricula.nota = round(float(nota), 2)
        self.guardar()
        return True, f"Nota {matricula.nota:.1f} registrada: {matricula.estado()}"

    def eliminar(self, id_matricula):
        """Retirar una matrícula: se borra y el cupo vuelve a la materia."""
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return False, f"No existe la matrícula {id_matricula}"
        materia = self.materias.obtener(matricula.materia_id)
        if materia is not None:
            materia.liberar_cupo()
            self.materias.guardar()
        self.lista.remove(matricula)
        self.guardar()
        return True, f"Matrícula {id_matricula} retirada y cupo devuelto"

    # --- propio de matrículas ---
    def retirar_matricula(self, id_matricula):
        return self.eliminar(id_matricula)

    def obtener_matriculas(self):
        return self.leer()

    def obtener_matricula(self, id_matricula):
        return self.obtener(id_matricula)

    def crear_matricula(self, datos):
        return self.crear(datos)

    def certificado(self, id_matricula):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return None
        # DICCIONARIOS ÍNDICE {id: objeto}: encontrar al estudiante y a la materia
        # es un acceso directo por clave, sin recorrer listas.
        indice_estudiantes = {e.id: e for e in self.estudiantes.leer()}
        indice_materias = {m.id: m for m in self.materias.leer()}
        estudiante = indice_estudiantes.get(matricula.estudiante_id)
        materia = indice_materias.get(matricula.materia_id)
        nota = "sin nota" if matricula.nota is None else f"{matricula.nota:.1f}"
        texto = f"CERTIFICADO #{matricula.id}   periodo: {matricula.periodo}\n"
        if estudiante:
            texto += f"Estudiante: {estudiante.nombre_completo()}   ({estudiante.carnet})\n"
        else:
            texto += "Estudiante: eliminado\n"
        if materia:
            texto += (f"Materia   : {materia.nombre}   ({materia.codigo}) "
                      f"· {materia.creditos} créditos\n")
        else:
            texto += "Materia   : eliminada\n"
        texto += "-" * 42 + "\n"
        texto += f"Nota      : {nota}\n"
        texto += f"Estado    : {matricula.estado()}"
        return texto

    def matriculas_por_estudiante(self):
        """DICCIONARIO de LISTAS: {estudiante_id: [matrículas de ese estudiante]}.
        Es la colección ideal para agrupar: la clave es el grupo y la lista guarda sus miembros."""
        agrupadas = {}
        for matricula in self.lista:
            agrupadas.setdefault(matricula.estudiante_id, []).append(matricula)
        return agrupadas

    def promedio_de_estudiante(self, id_estudiante):
        """Promedio de las matrículas con nota; None si todavía no tiene ninguna."""
        matriculas = self.matriculas_por_estudiante().get(id_estudiante, [])
        notas = [m.nota for m in matriculas if m.nota is not None]
        if not notas:
            return None
        return round(sum(notas) / len(notas), 2)

    def aprobadas(self):
        total = 0
        for matricula in self.lista:
            if matricula.esta_aprobada():
                total += 1
        return total
