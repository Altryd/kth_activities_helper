import {matchStruct} from "./page.jsx"

export default function CheckButton(props: {matchStruct: matchStruct, text: string}) {
    if (props.matchStruct.IsApproved) {
        return "";
    }
    return <button><b>{props.text}</b></button> // TODO
}