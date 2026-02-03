# Limiares de Temperatura para o Heatmap de Ofertas

# Percentagens de progresso (vendido / mínimo)
HEATMAP_THRESHOLDS = {
    'COLD': 30,      # < 30% = Frio (Azul)
    'WARM': 70,      # 30-70% = Aquecendo (Laranja)
    'HOT': 100       # > 70% = ON FIRE (Vermelho/Fogo)
}

# Cores para uso no Template (opcional, pode ser feito via CSS classes)
HEATMAP_COLORS = {
    'COLD': '#3498db',
    'WARM': '#f39c12',
    'HOT': '#e74c3c'
}
