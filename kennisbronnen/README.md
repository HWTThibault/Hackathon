# Kennisbronnen

De Kennisbronnen zitten in het Challenge pack: `https://mcp.findingsolutions.be/pack.zip`, open vanaf 10:00. Pak de map `kennisbronnen/` uit de zip hier uit. Via MCP zijn lokale bestanden niet nodig: `.env.example` bevat de paden voor alle zes Rollen.

Werk je zonder MCP, zet dan de bestanden van elke Rol in een eigen map:

```
kennisbronnen/
  oracle/
    <bestand>.md
  beast_master/
    <bestand>.md
    <bestand>.csv
```

De kit plakt de `.md`- en `.csv`-bestanden van een Rol in de prompt van dat Raadslid, als `MCP_<ROL>` in `.env` leeg is.
