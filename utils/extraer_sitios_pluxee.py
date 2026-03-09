from bs4 import BeautifulSoup
import pandas as pd

INPUT_HTML = "utils/locations-pluxee.html"
OUTPUT_MD = "files/results/tiendas.md"
OUTPUT_EXCEL = "files/results/tiendas_pluxee.xlsx"


def extraer_tiendas(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    tiendas = []

    # Cada tienda está dentro de un div con clase chakra-linkbox
    bloques = soup.find_all("div", class_="chakra-linkbox")

    for bloque in bloques:
        try:
            # Tipo (p con clase css-17odtil)
            tipo_tag = bloque.find("p", class_="chakra-text css-17odtil")
            tipo = tipo_tag.get_text(strip=True) if tipo_tag else None

            # Nombre (h2)
            nombre_tag = bloque.find("h2")
            nombre = nombre_tag.get_text(strip=True) if nombre_tag else None

            # Dirección y Ciudad
            address = bloque.find("address")
            direccion = None
            ciudad = None

            if address:
                ps = address.find_all("p")
                if len(ps) >= 2:
                    direccion = ps[0].get_text(strip=True)
                    ciudad = ps[1].get_text(strip=True)

            # Validación básica
            if nombre and direccion and ciudad and tipo:
                tiendas.append({
                    "nombre": nombre,
                    "direccion": direccion,
                    "ciudad": ciudad,
                    "tipo": tipo
                })

        except Exception as e:
            print(f"Error procesando bloque: {e}")

    return tiendas


def generar_markdown(tiendas, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for tienda in tiendas:
            f.write(f"## {tienda['nombre']}\n")
            f.write(f"- Dirección: {tienda['direccion']}\n")
            f.write(f"- Ciudad: {tienda['ciudad']}\n")
            f.write(f"- Tipo: {tienda['tipo']}\n\n")


def generar_excel(tiendas, output_path):
    df = pd.DataFrame(tiendas)
    df.to_excel(output_path, index=False)

if __name__ == "__main__":
    tiendas = extraer_tiendas(INPUT_HTML)
    generar_markdown(tiendas, OUTPUT_MD)
    generar_excel(tiendas, OUTPUT_EXCEL)
    print(f"Se generó el archivo {OUTPUT_MD} con {len(tiendas)} tiendas.")