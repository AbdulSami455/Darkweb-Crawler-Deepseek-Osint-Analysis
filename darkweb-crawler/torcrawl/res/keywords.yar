/*
    Yara.
*/

rule keyword_search
{
    meta:
        author = "@the-siegfried"
        score = 90

    strings:
        $a = "Keyword1" fullword wide ascii nocase
        $b = "Keyword Two" wide ascii nocase
        $c = "kw 3" ascii
        $d = "KEYWORD four" nocase
        $e = "google-" nocase

    condition:
        any of them
}


