import asyncio
import time

def sincrona():
    print("Inicio Sincrono")
    time.sleep(2)
    print("Fim sincrono")
    return "Resuldado sincrono"


async def assincrona():
    print("Inicio assincrono")
    await asyncio.sleep(2)
    print("Fim assincrono")
    return "Resuldado assincrono"

async def comparacao():
    print("Comparação sincrono e assincrono")

    inicio = time.time()
    sincrona()
    sincrona()

    tempo_sync = time.time() - inicio

    print(f"Tempo sincrono: {tempo_sync:.2f}s")

    inicio = time.time()

    await asyncio.gather(
        assincrona(),
        assincrona()

    )
    tempo_async = time.time() - inicio
    print(f"Tempo assincrono: {tempo_async:.2f}s")

asyncio.run(comparacao())