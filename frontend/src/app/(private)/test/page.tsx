import Menu from "@/src/components/Menu"
import Input from "@/src/components/ui/Input"

export default function TestPage (){
    return (
        <div className="h-full  bg-black flex gap-8 px-12 py-12">
            <div >
                <h2 className="text-slate-50 border">Menu ui </h2>
                <Menu/>
            </div>
            
            <div>
                <h2 className="text-slate-50">Input ui </h2>
                <Input label="Email" placeholder="Enter your email" type="email"/>
            </div>
            
        </div>

    )
}