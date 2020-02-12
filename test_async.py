import asyncio
import concurrent.futures
from random import choices
from statistics import mean

from modelmeta import DataFile, DataFileVariable, EnsembleDataFileVariables
from modelmeta import Ensemble
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contexttimer import Timer

from ce.api.util import open_nc, get_array

async def call_get_array(fname, var_name):
    area = ('POLYGON ((-129.492187 47.558593, -129.492187 52.050781, '
            '-122.167969 52.050781, -122.167969 47.558593, -129.492187 '
            '47.558593))')

    with open_nc(fname) as nc, Timer() as t:
        array = get_array(nc, fname, 0, area, var_name)
    return t.elapsed


async def main():
    engine = create_engine("postgresql://ce_meta_ro@db3/ce_meta")
    Session = sessionmaker(bind=engine)
    sesh = Session()

    results = sesh.query(
        DataFile.filename,
        DataFileVariable.netcdf_variable_name
    ).join(DataFileVariable).join(EnsembleDataFileVariables).join(Ensemble)\
     .filter(Ensemble.name=='ce_files').all()

    results = choices(results, k=10)
    tasks = []
    times = []

    #with concurrent.futures.ThreadPoolExecutor() as pool:
    #    tasks = [loop.run_in_executor(pool, call_get_array, fname, var_name)
    #             for fname, var_name in results]

    tasks = [loop.create_task(call_get_array(fname, var_name))
             for fname, var_name in results]

    await asyncio.wait(tasks)
    times = [t.result() for t in tasks]
    stats = (min(times), mean(times), max(times))
    return stats


if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        #loop.set_debug(1)
        stats = loop.run_until_complete(main())
        print(stats)
    except Exception:
        pass
    finally:
        loop.close()
