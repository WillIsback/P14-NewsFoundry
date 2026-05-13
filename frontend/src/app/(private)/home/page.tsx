import AssistantCard from "@/src/components/AssistantCard";
import Menu from "@/src/components/Menu";
import { ButtonSend } from "@/src/components/ui/ButtonSend";
import { ButtonSubMenu } from "@/src/components/ui/ButtonSubMenu";
import TextArea from "@/src/components/ui/TextArea";
import { promises as fs } from "node:fs";

export default async function TestPage() {
  let chats: { id: string; date: string }[] | undefined;
  let pressReviews:
    | { id: string; title: string; description: string; content: string }[]
    | undefined;
  let messages:
    | { id: string; type: "user" | "ai"; content: string; timestamp: string }[]
    | undefined;

  try {
    const file = await fs.readFile(
      `${process.cwd()}/data/mockData.json`,
      "utf8",
    );
    const data = JSON.parse(file);
    chats = data.chats;
    pressReviews = data.pressReviews;
    messages = data.messages;
  } catch {
    chats = undefined;
    pressReviews = undefined;
    messages = undefined;
  }

  console.log(chats);
  return (
    <div className="flex w-full h-full">
      <Menu chats={chats}/>
      {/* Main content area */}
      <div className=" w-full h-full flex flex-col">
        <header className="w-full h-22 flex items-center px-4.5 py-1.75 bg-slate-100 border-0 border-l border-b border-slate-400">
          <div className="w-fit h-fit flex items-center gap-2 rounded-[8px]">
            <ButtonSubMenu type_="chat" active />
            <ButtonSubMenu type_="review" />
          </div>
        </header>
        <section className="w-full min-h-202.75 flex flex-col gap-2.5 px-[25%] py-[18%] bg-slate-400"> 
          <AssistantCard />
        </section>
        <footer className="flex w-full min-h-23.25 gap-4 px-[6.44%] py-4.25 bg-white">
          <TextArea />
          <ButtonSend />
        </footer>
      </div>
    </div>
  )
}