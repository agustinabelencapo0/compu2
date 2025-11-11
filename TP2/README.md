# TP2 - Sistema de Scraping y Análisis Web Distribuido

## Estructura


TP2/
├── server_scraping.py          
├── server_processing.py        
├── client.py                   
├── scraper/
│   ├── __init__.py
│   ├── html_parser.py        
│   ├── metadata_extractor.py  
│   └── async_http.py        
├── processor/
│   ├── __init__.py
│   ├── screenshot.py           
│   ├── performance.py          
│   ├── image_processor.py     
│   └── advanced.py             
├── common/
│   ├── __init__.py
│   ├── protocol.py             
│   └── serialization.py        
├── tests/
│   ├── test_scraper.py
│   └── test_processor.py
├── requirements.txt
└── README.md


## Uso

1. Iniciar servidor de procesamiento:

```bash
python server_processing.py -i 127.0.0.1 -p 9000
```

2. Iniciar servidor de scraping:

```bash
python server_scraping.py -i 127.0.0.1 -p 8000 --proc-ip 127.0.0.1 --proc-port 9000
```

3. Ejecutar el cliente o consultar endpoints:

```bash
python client.py -i 127.0.0.1 -p 8000 -u https://example.com
```



