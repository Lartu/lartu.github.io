function run()
{
    var variables = {};
    variables["y"] = 0;
    $("#output-area").text("Running...");
    $("#output-area").css("color", "black");
    console.log("S Interpreter, by Martín del Río (lartu.net)");
    
    //Parse input area variables
    console.log("Evaluating input variables...");
    tokens = $('#input-area').val().split(",");
    for(var i = 0; i < tokens.length; ++i)
    {
        //Fix token name
        var token = tokens[i].trim().toLowerCase();
        if(token.length == 0) continue;
        //Get token parts
        var parts = token.split(":");
        if(parts.length != 2)
        {
            error("malformed input variable declaration: '" + token + "'");
            return;
        }
        var var_name = parts[0].trim();
        var var_value = parseInt(parts[1].trim());
        //Check if the variable has a valid name
        if(!is_valid_name('x', var_name))
        {
            error("malformed input variable name: '" + var_name + "' in '" + token + "'");
            return;
        }
        //Check if the value is valid
        if(var_value.length == 0 || !Number.isInteger(var_value))
        {
            error("malformed input variable value: '" + var_value + "' in '" + token + "'");
            return;
        }
        //If everything is alright, store the variable and its value
        variables[var_name] = var_value;
        console.log("- " + var_name + " = " + variables[var_name]);
    }
    
    //Parse code
    var lines = $('#code-area').val().split("\n");
    console.log("Cleaning program...");
    var newlines = [];
    //Remove empty lines, comments and style lines
    for(var i = 0; i < lines.length; ++i)
    {
        line = lines[i].trim().toLowerCase();
        if(line.indexOf("#") != -1)
            line = line.substring(0, line.indexOf("#"));
        if(line.length == 0) continue;
        newlines.push(line);
        console.log(" - " + line);
    }
    //Get labels
    console.log("Parsing labels...");
    var labels = {};
    labels["e"] = -1;
    for(var i = 0; i < newlines.length; ++i)
    {
        line = newlines[i];
        if(line[0] == "[")
        {
            if(line.indexOf("]") == -1)
            {
                error("malformed label on line '" + line + "'");
                return;
            }
            label_content = line.substring(1, line.indexOf("]"));
            if(!is_valid_name("*", label_content) || label_content=="e")
            {
                error("malformed label on line '" + line + "'");
                return;
            }
            console.log(" - label found: " + label_content + ": " + i);
            labels[label_content] = i;
            newlines[i] = line.substring(line.indexOf("]") + 1).trim();
        }
    }
    //Turn lines into IR
    console.log("Compiling program...");
    for(var i = 0; i < newlines.length; ++i)
    {
        line = newlines[i];
        tokens = line.split(" ");
        //Add or sub
        if(tokens.length == 5)
        {
            if(tokens[1] != "<-" || tokens[4] != "1" || tokens[0] != tokens[2])
            {
                error("malformed statement on line '" + line + "' (may include label)");
                return;
            }
            if(!is_valid_name("x", tokens[0]) && !is_valid_name("y", tokens[0]) && !is_valid_name("z", tokens[0]))
            {
                error("malformed variable name on line '" + line + "' (may include label)");
                return;
            }
            else
            {
                if(tokens[0][0] == "x" && !(tokens[0] in variables))
                {
                    error("undeclared input variable on line '" + line + "' (may include label)");
                    return;
                }
                if(tokens[3] == "+")
                    line = "+ " + tokens[0];
                else if(tokens[3] == "-")
                    line = "- " + tokens[0];
                else
                {
                    error("malformed statement on line '" + line + "' (may include label)");
                    return;
                }
            }
        }
        else if(tokens.length == 6)
        {
            if(tokens[0] != "if" || tokens[2] != "!=" || tokens[3] != "0" || tokens[4] != "goto" || !is_valid_name("*", tokens[5]))
            {
                error("malformed statement on line '" + line + "' (may include label)");
                return;
            }
            else
            {
                if(!is_valid_name("x", tokens[1]) && !is_valid_name("y", tokens[1]) && !is_valid_name("z", tokens[1]))
                {
                    error("malformed variable name on line '" + line + "' (may include label)");
                    return;
                }
                else
                {
                    if(tokens[1][0] == "x" && !(tokens[1] in variables))
                    {
                        error("undeclared input variable on line '" + line + "' (may include label)");
                        return;
                    }
                    line = "? " + tokens[1] + " " + tokens[5];
                }
            }
        }
        else
        {
            error("malformed statement on line '" + line + "' (may include label)");
            return;
        }
        newlines[i] = line;
        console.log(" - " + line);
    }
    //Show used variables
    console.log("Variables used:");
    for(i in variables){
        console.log(" - " + i);
    }
    //Show compiled program
    console.log("Compiled program:");
    for(i = 0; i < newlines.length; ++i)
    {
        console.log(" - " + newlines[i]);
    }
    //Run code
    console.log("Running program...");
    for(i = 0; i < newlines.length; ++i)
    {
        console.log(" - " + newlines[i]);
        line = newlines[i].split(" ");
        if(line[0] == "+")
        {
            if(!(line[1] in variables))
                variables[line[1]] = 0;
            ++variables[line[1]];
        }
        else if(line[0] == "-")
        {
            if(!(line[1] in variables))
                variables[line[1]] = 0;
            if(variables[line[1]] > 0) --variables[line[1]];
        }
        else if(line[0] == "?")
        {
            if(!(line[1] in variables))
                variables[line[1]] = 0;
            if(!(line[2] in labels))
                break;
            if(variables[line[1]] != 0)
                if(line[2] == "e") break;
                else i = labels[line[2]] - 1;
        }
    }
    console.log("Return value: " + variables["y"]);
    $("#output-area").text("Y = " + variables["y"]);
}

function is_valid_name(prefix, name)
{
    prefix = prefix.toLowerCase();
    if(name.length == 0) return false;
    if(prefix == "*" && !name[0].match(/[a-z]/i)) return false;
    if(prefix != "*" && name[0] != prefix) return false;
    tail = name.substring(1);
    if(prefix == "y" && tail.length > 0) return false;
    if(tail.length == 0) return true;
    tail = parseInt(tail);
    return Number.isInteger(tail);
}

function error(msg){
    $("#output-area").css("color", "red");
    $("#output-area").text("Error: " + msg + ".");
}
