"""Perfil de Hypothesis para a suite inteira.

NFR-P-21: `deadline=None`. As propriedades de U2 tocam disco de verdade, e o
prazo padrao de Hypothesis (200 ms por exemplo) transforma a variacao normal de
I/O em falha intermitente - o tipo de teste que se aprende a ignorar. O que
interessa aqui e a propriedade, nao o cronometro; o alvo de desempenho tem
medicao propria em test_sqlite.py.
"""

from hypothesis import HealthCheck, settings

settings.register_profile(
    "fishingrod",
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
settings.load_profile("fishingrod")
