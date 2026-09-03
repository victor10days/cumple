-- cumple QC: drop audio files or a delivery folder on this app to get a QC sheet.
-- Built by integrations/macos/build_app.sh, which fills in the path to cumple below.

property cumpleBin : "CUMPLE_BIN_PLACEHOLDER"
property defaultSpec : "netflix-2.0"

on run
	display dialog "Drop audio files or a delivery folder on this app to check them against a destination and open the QC sheet." & return & return & "cumple: " & cumpleBin buttons {"OK"} default button 1 with title "cumple QC"
end run

on open theItems
	set specId to chooseSpec()
	if specId is false then return
	repeat with anItem in theItems
		set p to POSIX path of anItem
		set cmd to quoted form of cumpleBin & " check " & quoted form of p & " --spec " & quoted form of specId & " --sheet --pdf"
		try
			do shell script cmd
		on error errMsg number errNum
			-- exit status 1 means FAIL, which is a result, not an error
			if errNum is not 1 then
				display dialog "cumple could not check " & p & ":" & return & errMsg buttons {"OK"} default button 1 with icon stop with title "cumple QC"
				return
			end if
		end try
		set sheetPath to sheetFor(p)
		do shell script "open " & quoted form of sheetPath
	end repeat
end open

on chooseSpec()
	try
		set specList to paragraphs of (do shell script quoted form of cumpleBin & " specs --ids")
	on error errMsg
		display dialog "cumple is not runnable at " & cumpleBin & ":" & return & errMsg buttons {"OK"} default button 1 with icon stop with title "cumple QC"
		return false
	end try
	set picked to choose from list specList with prompt "Check against which destination?" default items {defaultSpec} with title "cumple QC"
	if picked is false then return false
	return item 1 of picked
end chooseSpec

on sheetFor(p)
	-- the sheet sits next to the file (or inside a dropped folder), PDF preferred
	set shellCmd to "f=" & quoted form of p & "; f=\"${f%/}\"; if [ -d \"$f\" ]; then d=\"$f\"; s=$(basename \"$f\"); else d=$(dirname \"$f\"); s=$(basename \"${f%.*}\"); fi; if [ -f \"$d/$s.qc.pdf\" ]; then echo \"$d/$s.qc.pdf\"; else echo \"$d/$s.qc.html\"; fi"
	return do shell script shellCmd
end sheetFor
