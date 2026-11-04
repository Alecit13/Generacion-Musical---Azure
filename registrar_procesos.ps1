<#
Registra el uso de CPU por proceso cada ~1 s hasta Ctrl+C (H6; paso 9 de docs/MEDICIONES.md).
Uso (en una terminal aparte, antes de lanzar main.py):
    powershell -ExecutionPolicy Bypass -File registrar_procesos.ps1 sesiones\procesos_<corrida>.csv
Columnas: t_local, proceso, pid, cpu_pct. cpu_pct es % de UN núcleo lógico (este equipo tiene 12: máximo 1200 %).
Se guardan los procesos con cpu_pct >= $Minimo y siempre python y chrome. Los contadores se consultan en cada
muestra, así aparecen también los procesos que arrancan después (python). El pid distingue procesos con el mismo
nombre (chrome, chrome#1, ...). Este script también aparece en el registro (powershell): es su propio costo.
#>
param(
    [Parameter(Mandatory = $true)][string]$Salida,
    [double]$Minimo = 0.5,
    [int]$Muestras = 0          # 0 = hasta Ctrl+C (solo para probar se pone un número)
)
$rutas = '\Proceso(*)\% de tiempo de procesador', '\Proceso(*)\Id. de proceso'
$inv = [Globalization.CultureInfo]::InvariantCulture      # punto decimal aunque Windows esté en español
$w = [System.IO.StreamWriter]::new($Salida, $false, [System.Text.UTF8Encoding]::new($false))
$w.WriteLine("t_local,proceso,pid,cpu_pct"); $w.Flush()
$n = 0
try {
    while ($Muestras -eq 0 -or $n -lt $Muestras) {
        $m = Get-Counter $rutas -SampleInterval 1 -MaxSamples 1 -ErrorAction SilentlyContinue
        if (-not $m) { continue }
        $n++
        $t = $m.Timestamp.ToString("yyyy-MM-dd HH:mm:ss.fff", $inv)
        $pids = @{}; $pct = @{}
        foreach ($s in $m.CounterSamples) {
            if ($s.Path -notmatch 'proceso\((.+)\)\\') { continue }
            $inst = $Matches[1]
            if ($s.Path -like '*id. de proceso') { $pids[$inst] = [int]$s.CookedValue } else { $pct[$inst] = $s.CookedValue }
        }
        foreach ($k in $pct.Keys) {
            if ($k -in '_total', 'idle') { continue }
            $v = $pct[$k]
            if ($v -ge $Minimo -or $k -like 'python*' -or $k -like 'chrome*') {
                $w.WriteLine("$t,$k,$($pids[$k]),$($v.ToString('0.0', $inv))")
            }
        }
        $w.Flush()                # cada muestra queda en disco aunque se corte con Ctrl+C
    }
} finally {
    $w.Close()
}
