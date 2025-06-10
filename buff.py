from buffxSteamComparison import run


UPDATE_BUFF = True
UPDATE_STEAM = True
UPDATE_CSFLOAT = True
UPDATE_BUFF = False
UPDATE_STEAM = False
UPDATE_CSFLOAT = False

run(UPDATE_BUFF, UPDATE_STEAM, UPDATE_CSFLOAT, graph=True)
