// app/api/proxy/[...path]/route.js
import { NextResponse } from 'next/server';
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";


async function handleRequest(request: Request, { params }: { params: { path: string[] } }, method: string) {
  const session = await getServerSession(authOptions);
  const paramsAwait = await params;
  const path = paramsAwait.path.join('/');
  
  const headers = new Headers(request.headers);
  
  if (session?.APIToken) {
    headers.set('Authorization', `Bearer ${session.APIToken.accessToken}`);
  }
  
  const response = await fetch(`${process.env.API_URL}/${path}`, {
    method,
    headers,
    body: method !== 'GET' ? await request.blob() : undefined,
  });


  console.log("HEADERS");
  console.log(headers);
  console.log("RESPONSE");
  console.log(response);
  
  return new NextResponse(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
}

export const dynamic = 'force-dynamic';


export async function GET(request: Request, { params }: { params: { path: string[] } }) {
  return handleRequest(request, { params }, 'GET');
}

export async function POST(request: Request, { params }: { params: { path: string[] } }) {
  return handleRequest(request, { params }, 'POST');
}

export async function PUT(request: Request, { params }: { params: { path: string[] } }) {
  return handleRequest(request, { params }, 'PUT');
}

export async function DELETE(request: Request, { params }: { params: { path: string[] } }) {
  return handleRequest(request, { params }, 'DELETE');
}