import pandas as pd
def clasify_estado_general(row):
    if row['estado_os_cable'] is None:
        row['estado_os_cable'] = ''
    if row['estado_os_internet'] is None:
        row['estado_os_internet'] = ''
    estado_combinado = f"{row['estado_os_internet']} - {row['estado_os_cable']}"
    if estado_combinado == 'ANULADA - ANULADA':
        return 'ANULADA'
    if 'ANULADA' in estado_combinado and 'PENDIENTE' not in estado_combinado and 'DESCARGADA' not in estado_combinado:
        return 'ANULADA'
    if 'DESCARGADA' in estado_combinado:
        return 'DESCARGADA'
    if 'PENDIENTE' in estado_combinado and 'ANULADA' in estado_combinado:
        return 'PENDIENTE'
    return 'PENDIENTE'
    
df = pd.read_excel('files/source/estados.xlsx')
df['estado_general'] = df.apply(clasify_estado_general, axis=1)
df.to_excel('files/results/estados_clasificados.xlsx', index=False)