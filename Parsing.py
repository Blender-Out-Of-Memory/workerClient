class ParsingException(Exception):
    MemberName: str
    Value: object
    TargetType: type
    def __init__(self, memberName: str, value, targetType: type):
        valueStr = str(value)
        if len(valueStr) < 15:
            valueStr = f"{valueStr[:15]}..."

        super().__init__(f"Failed parsing {valueStr} to {str(targetType)} for member {memberName}")

        self.MemberName = memberName
        self.Value = value
        self.TargetType = targetType

def try_to_int(string: str, memberName: str) -> int:
    try:
        return int(string)
    except:
        raise ParsingException(memberName, string, int)
