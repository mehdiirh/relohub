function intComma(value) {
    return value.toString().split(/(?=(?:...)*$)/)
}

function intSpaceCardNumber(value) {
    return value.toString().split(/(?=(?:....)*$)/).toString().replaceAll(",", " ")
}