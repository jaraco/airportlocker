
{	
	"project" : "Hello World",
	"css-url" : "styles.css",
	"pages"   :
	[
		{
			"title" : "Introduction",
			"file"  : "intro"
		},
		{
			"title" : "Internals",
			"file"  : "int",
			"children" : 
			[
				{
					"title" : "Lexer",
					"file"  : "int-lex"
				},
				{
					"title" : "Parser",
					"file"  : "int-parse"
				}
			]
		}
	]
}
